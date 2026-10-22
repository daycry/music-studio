"""Loaders locales seguros. Importación de torch diferida al proceso hijo."""

import gc
import inspect
import json
import math
import os
from pathlib import Path

from engine_common import EngineError
from engine_common.runtime import NvmlGpu

from .descriptor import read_lock, validate_language
from .safety import verify_model


def gpu_snapshot():
    return NvmlGpu().snapshot()


def clap_text_budget(processor, config, text):
    tokens = processor.tokenizer(text, truncation=False, add_special_tokens=True)[
        "input_ids"
    ]
    limit = (
        config.text_config.max_position_embeddings - 2
    )  # RoBERTa reserva sus posiciones iniciales.
    if len(tokens) > limit:
        raise EngineError(
            "INVALID_PARAMS", "Texto supera el presupuesto de CLAP; no se trunca"
        )
    return len(tokens), limit


class LocalBackend:
    def __init__(self, models_dir):
        self.models_dir = Path(models_dir)
        self.model = self.processor = None
        self.model_id = None
        self.device = "cpu"
        self.peak_mb = self.cap_mb = 0

    def load(self, model_id, mode, cap_mb, total_mb):
        if self.model is not None:
            raise EngineError("BUSY", "El modelo anterior debe descargarse")
        directory, weights = verify_model(self.models_dir, model_id)
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        self.device = "cpu" if model_id == "beat-this" else "cuda:0"
        import torch

        if self.device != "cpu":
            if not torch.cuda.is_available():
                raise EngineError("VRAM_EXCEEDED", "GPU no disponible")
            measured_total, free = gpu_snapshot()
            margin = int(os.getenv("STUDIO_VRAM_MARGIN_MB", "512"))
            if margin < 0:
                raise EngineError("INVALID_PARAMS", "Margen VRAM inválido")
            self.cap_mb = min(cap_mb, max(0, free - margin))
            if measured_total <= 0 or self.cap_mb <= 0:
                raise EngineError("VRAM_EXCEEDED")
            torch.cuda.set_per_process_memory_fraction(self.cap_mb / measured_total)
            torch.cuda.reset_peak_memory_stats()
        try:
            if model_id.startswith("qwen3-"):
                self._load_qwen(directory, model_id)
            elif model_id == "clap-larger-music":
                self._load_clap(directory, weights)
            elif model_id == "audiobox-aesthetics":
                self._load_aesthetics(directory, weights)
            else:
                self._load_beats(directory, weights)
            self.model_id = model_id
            self.observe_peak()
        except EngineError:
            self.release()
            raise
        except Exception as error:  # noqa: BLE001 - frontera upstream, mensaje público estable
            self.release()
            code = (
                "VRAM_EXCEEDED"
                if "out of memory" in str(error).lower()
                else "WEIGHTS_MISMATCH"
            )
            raise EngineError(code, "No se pudo cargar el modelo local") from None

    def _load_qwen(self, directory, model_id):
        import torch
        from qwen_asr import Qwen3ASRModel, Qwen3ForcedAligner
        from qwen_asr.inference.qwen3_forced_aligner import Qwen3ForceAlignProcessor
        from transformers import AutoModel, AutoProcessor

        model, info = AutoModel.from_pretrained(
            str(directory),
            local_files_only=True,
            use_safetensors=True,
            trust_remote_code=False,
            dtype=torch.bfloat16,
            device_map=self.device,
            attn_implementation="sdpa",
            output_loading_info=True,
        )
        if any(
            info.get(key)
            for key in (
                "missing_keys",
                "unexpected_keys",
                "mismatched_keys",
                "error_msgs",
            )
        ):
            del model
            raise EngineError(
                "WEIGHTS_MISMATCH", "Tensores Qwen no coinciden con la arquitectura"
            )
        processor = AutoProcessor.from_pretrained(
            str(directory),
            local_files_only=True,
            trust_remote_code=False,
            fix_mistral_regex=True,
        )
        if model_id == "qwen3-asr-1.7b":
            self.model = Qwen3ASRModel(
                backend="transformers",
                model=model,
                processor=processor,
                sampling_params=None,
                forced_aligner=None,
                max_inference_batch_size=1,
                max_new_tokens=4096,
            )
        else:
            self.model = Qwen3ForcedAligner(
                model=model,
                processor=processor,
                aligner_processor=Qwen3ForceAlignProcessor(),
            )

    def _load_clap(self, directory, weights):
        import torch
        from safetensors.torch import load_file
        from transformers import ClapConfig, ClapModel, ClapProcessor

        config = ClapConfig.from_pretrained(str(directory), local_files_only=True)
        model = ClapModel(config)
        model.load_state_dict(load_file(str(weights[0]), device="cpu"), strict=True)
        self.model = model.to(device=self.device, dtype=torch.bfloat16).eval()
        self.processor = ClapProcessor.from_pretrained(
            str(directory), local_files_only=True, trust_remote_code=False
        )

    def _load_aesthetics(self, directory, weights):
        import torch
        from audiobox_aesthetics.infer import AesPredictor, Normalize
        from audiobox_aesthetics.model.aes import AesMultiOutput
        from safetensors.torch import load_file

        config = json.loads((directory / "config.json").read_text())
        config["precision"] = "bf16"
        model = AesMultiOutput(**config)
        model.load_state_dict(load_file(str(weights[0]), device="cpu"), strict=True)
        # El código fijado compara str(torch.dtype) con "bf16" y deja autocast apagado.
        model.enable_autocast = True
        # Construir sin __post_init__/setup_model: esas recetas usan pickle o red.
        predictor = object.__new__(AesPredictor)
        predictor.model = model.to(device=self.device, dtype=torch.bfloat16).eval()
        predictor.device, predictor.data_col, predictor.sample_rate = (
            self.device,
            "path",
            16000,
        )
        predictor.target_transform = {
            axis: Normalize(**values)
            for axis, values in config["target_transform"].items()
        }
        self.model = predictor

    def _load_beats(self, directory, weights):
        import torch
        from beat_this.inference import Audio2Beats
        from beat_this.model.beat_tracker import BeatThis
        from beat_this.model.postprocessor import Postprocessor
        from beat_this.preprocessing import LogMelSpect
        from safetensors.torch import load_file

        config = json.loads(
            (Path(__file__).parent / "resources" / "beat_this.json").read_text()
        )
        if (
            config["checkpoint_sha256"]
            != read_lock(self.models_dir)["beat-this"]["file"]["sha256"]
        ):
            raise EngineError(
                "WEIGHTS_MISMATCH", "Configuración de beats pertenece a otro checkpoint"
            )
        kwargs = {
            key: value
            for key, value in config["hyper_parameters"].items()
            if key in inspect.signature(BeatThis).parameters
        }
        model = BeatThis(**kwargs)
        state = load_file(str(weights[0]), device="cpu")
        state = {key.removeprefix("model."): value for key, value in state.items()}
        model.load_state_dict(state, strict=True)
        predictor = object.__new__(Audio2Beats)
        predictor.device, predictor.float16 = torch.device("cpu"), False
        predictor.model = model.to("cpu").eval()
        predictor.spect = LogMelSpect(device="cpu")
        predictor.frames2beats = Postprocessor(type="minimal")
        self.model = predictor

    def observe_peak(self):
        if self.device != "cpu":
            import torch

            current_peak = torch.cuda.max_memory_allocated() / 1024**2
            self.peak_mb = max(self.peak_mb, current_peak)
            if current_peak > self.cap_mb:
                raise EngineError("VRAM_EXCEEDED")

    def release(self):
        self.model = self.processor = None
        gc.collect()
        if self.device != "cpu":
            import torch

            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        self.model_id = None

    def run(self, task, audio, params):
        import numpy as np
        import soundfile as sf
        import torch

        if task in {"audio.transcribe", "audio.align_lyrics"}:
            validate_language(params.get("language"))
        try:
            waveform, sample_rate = sf.read(audio, dtype="float32", always_2d=True)
        except sf.LibsndfileError as error:
            # SF_ERR_SYSTEM (2) indica un fallo del sistema, no de decodificación.
            if error.code == 2:
                raise
            raise EngineError("INVALID_PARAMS", "Audio no decodificable") from None
        if (
            not 0 < len(waveform) / sample_rate <= 600
            or not np.isfinite(waveform).all()
        ):
            raise EngineError(
                "INVALID_PARAMS", "Audio vacío, demasiado largo o inválido"
            )
        mono = waveform.mean(axis=1)
        with torch.inference_mode():
            if task == "audio.transcribe":
                from qwen_asr.inference.utils import merge_languages

                segments = []
                step = 180 * sample_rate
                for start in range(0, len(mono), step):
                    end = min(start + step, len(mono))
                    result = self.model.transcribe(
                        audio=(mono[start:end], sample_rate),
                        language=params.get("language"),
                        return_time_stamps=False,
                    )[0]
                    segments.append(
                        {
                            "start_s": start / sample_rate,
                            "end_s": end / sample_rate,
                            "text": result.text,
                            "language": result.language,
                        }
                    )
                output = {
                    "text": "".join(segment["text"] for segment in segments),
                    "language": merge_languages(
                        [segment["language"] for segment in segments]
                    ),
                    "segments": segments,
                }
            elif task == "audio.align_lyrics":
                segments = params.get("segments")
                if segments is None:
                    if len(mono) / sample_rate > 180:
                        raise EngineError(
                            "INVALID_PARAMS",
                            "Alineación independiente limitada a 180 s hasta M3",
                        )
                    segments = [
                        {
                            "start_s": 0,
                            "end_s": len(mono) / sample_rate,
                            "text": params["text"],
                            "language": params["language"],
                        }
                    ]
                words = []
                for segment in segments:
                    # Los silencios conservan su intervalo sin pedir timestamps inexistentes.
                    if not segment["text"].strip():
                        continue
                    start = round(segment["start_s"] * sample_rate)
                    end = round(segment["end_s"] * sample_rate)
                    if (
                        not 0 <= start < end <= len(mono)
                        or end - start > 180 * sample_rate
                    ):
                        raise EngineError("INTERNAL", "Fragmento reconocido inválido")
                    result = self.model.align(
                        audio=(mono[start:end], sample_rate),
                        text=segment["text"],
                        language=segment["language"],
                    )[0]
                    for word in result:
                        if (
                            not 0
                            <= word.start_time
                            <= word.end_time
                            <= (end - start) / sample_rate
                        ):
                            raise EngineError(
                                "INTERNAL", "Tiempos fuera del fragmento reconocido"
                            )
                        words.append(
                            {
                                "text": word.text,
                                "start_s": float(word.start_time) + start / sample_rate,
                                "end_s": float(word.end_time) + start / sample_rate,
                            }
                        )
                output = {"words": words}
            elif task == "audio.clap":
                import librosa

                count, limit = clap_text_budget(
                    self.processor, self.model.config, params["text"]
                )
                samples = (
                    librosa.resample(mono, orig_sr=sample_rate, target_sr=48000)
                    if sample_rate != 48000
                    else mono
                )
                audio_values = self.processor.feature_extractor(
                    samples,
                    sampling_rate=48000,
                    return_tensors="pt",
                    padding="repeatpad",
                    truncation=self.processor.feature_extractor.truncation,
                )
                text_values = self.processor.tokenizer(
                    [params["text"]],
                    return_tensors="pt",
                    padding=True,
                    truncation=False,
                )
                values = {**audio_values, **text_values}
                values = {
                    key: value.to(device=self.device, dtype=torch.bfloat16)
                    if value.is_floating_point()
                    else value.to(self.device)
                    for key, value in values.items()
                }
                result = self.model(**values)
                score = torch.nn.functional.cosine_similarity(
                    result.audio_embeds.float(), result.text_embeds.float()
                ).item()
                output = {
                    "score": score,
                    "text_tokens": count,
                    "text_token_limit": limit,
                    "text_truncated": False,
                    "audio_duration_s": len(samples) / 48000,
                    "audio_window_s": self.processor.feature_extractor.nb_max_samples
                    / self.processor.feature_extractor.sampling_rate,
                }
            elif task == "audio.aesthetics":
                output = self.model.forward(
                    [
                        {
                            "path": torch.from_numpy(mono).unsqueeze(0),
                            "sample_rate": sample_rate,
                        }
                    ]
                )[0]
            else:
                beats, downbeats = self.model(mono, sample_rate)
                intervals = np.diff(beats)
                if len(intervals) == 0 or np.any(intervals <= 0):
                    raise EngineError("INTERNAL", "No se detectaron beats suficientes")
                output = {
                    "bpm": float(60 / np.median(intervals)),
                    "beats_s": [float(value) for value in beats],
                    "downbeats_s": [float(value) for value in downbeats],
                }
        self.observe_peak()
        if not finite_values(output):
            raise EngineError("INTERNAL", "Resultado numérico inválido")
        return output


def finite_values(value):
    if isinstance(value, dict):
        return all(finite_values(item) for item in value.values())
    if isinstance(value, list):
        return all(finite_values(item) for item in value)
    return not isinstance(value, float) or math.isfinite(value)
