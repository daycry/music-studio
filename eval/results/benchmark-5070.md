# Benchmark RTX 5070

Sesión: `01M4KG1EQ2D9TEWFEZYR4RRV19`.

VRAM en reposo (NVML, plan): usada=null MiB; libre=null MiB. Las columnas idle son la mediana de observaciones previas por grupo; cap pertenece al proceso y shared al ámbito WDDM.

Tiempos en segundos; memoria en MiB. `run_s` incluye carga; RTF usa el reloj directo sincronizado. Caché de filesystem no controlada.

| config_id | duration_s | storage | phase | repetition | status | vram_peak_mb | vram_cap_mb | load_s | copy_s | idle_vram_used_mb | idle_vram_free_mb | shared_baseline_mb | inference_s | audio_duration_s | rtf | shared_gpu_peak_mb | wsl_mem_available_mb | rtf_ratio | spilled_engine | shared_gpu_observed | spill_assessment | run_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| turbo-lm06 | 30 | bind | process_cold | 0 | done | 7815.6685 | 10417.3398 | 96.2338 | 0 | 1014.0000 | 10930.0000 | 76.9414 | 18.1056 | 30.0000 | 0.6035 | 167.0391 | 11295.9453 | null | false | true | unknown | 01M4KG1EQ24Q539M88X5MYKNVS |
| turbo-lm06 | 30 | bind | warm | 1 | done | 7899.4795 | 10417.3398 | 0.0000 | 0 | 1014.0000 | 10930.0000 | 76.9414 | 5.0438 | 30.0000 | 0.1681 | 167.8008 | 10543.3242 | null | false | true | unknown | 01M4KG1EQ2QWDHQ50YW9MMXNFJ |
| turbo-lm06 | 30 | bind | warm | 2 | done | 7899.9839 | 10417.3398 | 0.0000 | 0 | 1014.0000 | 10930.0000 | 76.9414 | 5.1618 | 30.0000 | 0.1721 | 167.4766 | 10440.2070 | null | false | true | unknown | 01M4KG1EQ2F3DT83AQFSA4N3X7 |
| turbo-lm06 | 30 | bind | warm | 3 | done | 7898.8120 | 10417.3398 | 0.0000 | 0 | 1014.0000 | 10930.0000 | 76.9414 | 5.2894 | 30.0000 | 0.1763 | 167.4766 | 10348.3281 | null | false | true | unknown | 01M4KG1EQ2N1Y9V3Y5TX63B6SP |
| turbo-lm06 | 30 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2WT2VFZVXWG9CM122 |
| turbo-lm06 | 30 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2CQZS5CZASSD4JKW8 |
| turbo-lm06 | 30 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2FQ4BVZEKW74267YV |
| turbo-lm06 | 30 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2K1R9VY7MBY878WZX |
| turbo-lm06 | 60 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ25AHTPR8V4PP5Z42T |
| turbo-lm06 | 60 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2326T96204CTX316P |
| turbo-lm06 | 60 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ21N5JHAEBHMRZ8MD9 |
| turbo-lm06 | 60 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2X2NVG99F82VPZK3B |
| turbo-lm06 | 60 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2CGQBB0GXQ3H2ZMJ9 |
| turbo-lm06 | 60 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2WMJRSTP0GTBECK98 |
| turbo-lm06 | 60 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2JH2VCSYDJ9T19HD2 |
| turbo-lm06 | 60 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ254E5EVT7KWTKXEFV |
| turbo-lm06 | 180 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2MQ39939XRRGZW5N8 |
| turbo-lm06 | 180 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2W6MTXTEXQ54F0K3A |
| turbo-lm06 | 180 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2WKEA9BYJZGKFCMVA |
| turbo-lm06 | 180 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2AZYMXRTS4EM167FD |
| turbo-lm06 | 180 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2FC8HKP7ZVVGC18J6 |
| turbo-lm06 | 180 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2DJCX5FD9X70CFP4P |
| turbo-lm06 | 180 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ299B0QGAWEFXKXX2S |
| turbo-lm06 | 180 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ21S9SZ88EVPFZ80QK |
| turbo-lm06 | 300 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ24VZ0MG9FX3VKSJDM |
| turbo-lm06 | 300 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2R7XMAGGKVSFZR030 |
| turbo-lm06 | 300 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2B4AKWPGN4675YZEC |
| turbo-lm06 | 300 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ2B8BJN4SC1R1GGH1Y |
| turbo-lm06 | 300 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3ZXP7P5P05JJVJ0GE |
| turbo-lm06 | 300 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3EV1ZS65MZ17QXMRK |
| turbo-lm06 | 300 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3D3N145FPFGTCWE0A |
| turbo-lm06 | 300 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3ZR1T0W55M4DPE8BY |
| turbo-lm17 | 30 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ37X4DDKCSY0JQTFB6 |
| turbo-lm17 | 30 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3TAX2F847MF81ESM4 |
| turbo-lm17 | 30 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3XQZ35HVNADFJCVRW |
| turbo-lm17 | 30 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3K934186FRTG2YHY7 |
| turbo-lm17 | 30 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ32778M7CGJMQVT5GJ |
| turbo-lm17 | 30 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3C3FTJRZFE0SNK2V9 |
| turbo-lm17 | 30 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ38VMCJT3F1CWEKW6K |
| turbo-lm17 | 30 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3MZ51R817CG73GT4Z |
| turbo-lm17 | 60 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3DXTNNHBF26WD1306 |
| turbo-lm17 | 60 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3SHEEPSWKVFF6E5M0 |
| turbo-lm17 | 60 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3B20PP9C6BSP6WW4Z |
| turbo-lm17 | 60 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3G4X55TTZDFVH4P4J |
| turbo-lm17 | 60 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3ETP36ZZK4J5H7C5S |
| turbo-lm17 | 60 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3MN5DV817RRCBYT22 |
| turbo-lm17 | 60 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3C2P51R55BH4XQNDX |
| turbo-lm17 | 60 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3JG0KXH3NGESYF7D5 |
| turbo-lm17 | 180 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3F3VY3MV73ERP56T8 |
| turbo-lm17 | 180 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3KQWSATRNMHT6J3RT |
| turbo-lm17 | 180 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3H3SGVQYWYCYV5YHG |
| turbo-lm17 | 180 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3Y7NANQP2352K1PDB |
| turbo-lm17 | 180 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ37KW4YRJ1Z9BG71AH |
| turbo-lm17 | 180 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ37NM1SF3M70SZXMDY |
| turbo-lm17 | 180 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ39XECBMD9NETEGCYS |
| turbo-lm17 | 180 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ34WVDNDVZJ3RME2Q6 |
| turbo-lm17 | 300 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3H5XRDX5X47SEYZV2 |
| turbo-lm17 | 300 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3F0YE32Z3ZGSBEPA4 |
| turbo-lm17 | 300 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3GPWC7GBXVESN8GRS |
| turbo-lm17 | 300 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ383H3AGGR8WHM9GYY |
| turbo-lm17 | 300 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3R7TK4F71XS0N9FXF |
| turbo-lm17 | 300 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ36JZDQ72ATTAZYMJA |
| turbo-lm17 | 300 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3JPFEWTXQSQY9266P |
| turbo-lm17 | 300 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ32ZFVTP4XJ77N01FX |
| sft-lm06 | 30 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ32G0PNCPYVJMKHXFR |
| sft-lm06 | 30 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3B6A5TE86NQNZ4K4N |
| sft-lm06 | 30 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3BWRSTCTQCQXQ6PD8 |
| sft-lm06 | 30 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3PHW5R4A753RTNSX7 |
| sft-lm06 | 30 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ31TFWFGXWV5YBQYJJ |
| sft-lm06 | 30 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3NC57R024HNFJHSSC |
| sft-lm06 | 30 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3FAPVEQGW5D1TAXNE |
| sft-lm06 | 30 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3FJKJ5SGRGW6Y671Y |
| sft-lm06 | 60 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3ZDXNA81YB6J4Y37H |
| sft-lm06 | 60 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3ZN3QAG31S9VWVQY8 |
| sft-lm06 | 60 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3JAET8DQMZ7BYC4JM |
| sft-lm06 | 60 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3SHQARV6XRFZ9NWQV |
| sft-lm06 | 60 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3MH7P1Z9ZMD6BVTKN |
| sft-lm06 | 60 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3DEPM2XQ4DY4P7HC7 |
| sft-lm06 | 60 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3WR3QF2D0SGFF5W6W |
| sft-lm06 | 60 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3J79FDF1A51DDHGBG |
| sft-lm06 | 180 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ31CSGW6GXCB0KA45J |
| sft-lm06 | 180 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3Q7B9MT2GJV8WP4EF |
| sft-lm06 | 180 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3256KS8NYJ21QCYN4 |
| sft-lm06 | 180 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3X3S6H68AVQDEMJ11 |
| sft-lm06 | 180 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3Q38Z7KGEF94QXAMD |
| sft-lm06 | 180 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3TE19SGFHACXZ9EKA |
| sft-lm06 | 180 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ36BWXN0GQTEQSV3JK |
| sft-lm06 | 180 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3D4QX9S9DBCE4Z4ZA |
| sft-lm06 | 300 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ31AHY4WN99ZAM5QFW |
| sft-lm06 | 300 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ35ZBPCMP6B3MT7AJ1 |
| sft-lm06 | 300 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ39HYVQHZZ1NPFSS9Z |
| sft-lm06 | 300 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3XZCK0N9RSSSXSQ0G |
| sft-lm06 | 300 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3QF65RS5SERJK3NNB |
| sft-lm06 | 300 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ38HVH48PX6T5GNJN7 |
| sft-lm06 | 300 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3QDG2QX0EV45M9ZJ8 |
| sft-lm06 | 300 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ31E4ZJ6P9XS5X4AAD |
| base-lm06 | 30 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ327KV7RXE9RJ4W20G |
| base-lm06 | 30 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3864P0CQWZRDCVBC5 |
| base-lm06 | 30 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ31YWXK1JK877RDX43 |
| base-lm06 | 30 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3PNH376KRCKTJKSXF |
| base-lm06 | 30 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ38NZQPBZ48Y0FN07H |
| base-lm06 | 30 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3W7Q11JYP0T1A07A6 |
| base-lm06 | 30 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ33BCH0ES90FKQJ72V |
| base-lm06 | 30 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3V60ATF1E32TSVQGK |
| base-lm06 | 60 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3QN8G71B40JH1KHA5 |
| base-lm06 | 60 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3Z8J5075466PHGR60 |
| base-lm06 | 60 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3BY9JRKN3QM22S908 |
| base-lm06 | 60 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3TSZS0QGJ2F3Y8A5D |
| base-lm06 | 60 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3N2FYTVDJBD5X9VT6 |
| base-lm06 | 60 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3JW7BZ89VZ6A038B1 |
| base-lm06 | 60 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ31HEXGSFX4F01S6NS |
| base-lm06 | 60 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ30M3CDGV0XYR31VT0 |
| base-lm06 | 180 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3SVF4R706H4DV7ZBC |
| base-lm06 | 180 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ394N2YZ83DTN22ZDT |
| base-lm06 | 180 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3CRBGT5R234N78BYE |
| base-lm06 | 180 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3CPBSA3WF2CPTD0DG |
| base-lm06 | 180 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ358838357BA3GMK9T |
| base-lm06 | 180 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3P0CHGRWK2Y3DPQMF |
| base-lm06 | 180 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3006MABM2XA766TAM |
| base-lm06 | 180 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3ZEG1T723DXC0W77H |
| base-lm06 | 300 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3H9MK44QYWE4CA49Z |
| base-lm06 | 300 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3531TNA9FW9D3SSXJ |
| base-lm06 | 300 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3VZK541DS70K97FAV |
| base-lm06 | 300 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3F86QRCZ9TFKYV392 |
| base-lm06 | 300 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3V191Q9D9FC2C31F1 |
| base-lm06 | 300 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3NC78NSW3CVNJ6VE0 |
| base-lm06 | 300 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ326S1X3PGN8SDK4H8 |
| base-lm06 | 300 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3FZ3DZGJSVQA70HBV |
| xl-turbo-lm06-int8 | 30 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3MNMMWRZC4DFZ0VWT |
| xl-turbo-lm06-int8 | 30 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3BWW8D2137EKYWM54 |
| xl-turbo-lm06-int8 | 30 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ31W3MVJJXQA4829JC |
| xl-turbo-lm06-int8 | 30 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3QD2A84MFM9GZGTG4 |
| xl-turbo-lm06-int8 | 30 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3SKMQTMKYYAVT5TNS |
| xl-turbo-lm06-int8 | 30 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ301WTMX4N8DMWXERF |
| xl-turbo-lm06-int8 | 30 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3YK8SRFJHCZ3P12Q1 |
| xl-turbo-lm06-int8 | 30 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ35FJ0QRH83WNWFCN9 |
| xl-turbo-lm06-int8 | 60 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3QV7E1K94X4R8HQE9 |
| xl-turbo-lm06-int8 | 60 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3XHDVGMT27ZS1YNF6 |
| xl-turbo-lm06-int8 | 60 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ32MP79N8EZ3F5VT1K |
| xl-turbo-lm06-int8 | 60 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3T33V0DN9NBKHPEG3 |
| xl-turbo-lm06-int8 | 60 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3EGSCENS5CKC5NKPK |
| xl-turbo-lm06-int8 | 60 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3ESAXAHDWK601HJ61 |
| xl-turbo-lm06-int8 | 60 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3K9V4RES1K042PZXC |
| xl-turbo-lm06-int8 | 60 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ31QR0ZCJ7ZGSMV35Z |
| xl-turbo-lm06-int8 | 180 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3M41QB4B10ZHZHE7C |
| xl-turbo-lm06-int8 | 180 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3NN96YZCG6V64Y5BC |
| xl-turbo-lm06-int8 | 180 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3H2SF92Z8CFHGCXET |
| xl-turbo-lm06-int8 | 180 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3CHGZH5JRNX60W9BF |
| xl-turbo-lm06-int8 | 180 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ379ZART192QV7SMBR |
| xl-turbo-lm06-int8 | 180 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3YXFCCPVZ91KJDPR9 |
| xl-turbo-lm06-int8 | 180 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3Z976925W1QQA5584 |
| xl-turbo-lm06-int8 | 180 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ32A4ZP9QZXADJ1Y6Y |
| xl-turbo-lm06-int8 | 300 | container_copy | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3V2Q9YK4CVG6JDN12 |
| xl-turbo-lm06-int8 | 300 | container_copy | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3AA410JVVYDHY2B03 |
| xl-turbo-lm06-int8 | 300 | container_copy | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3JXGSJAKFYDA9DM6Q |
| xl-turbo-lm06-int8 | 300 | container_copy | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3TXQXBMNV1ZFG3RGP |
| xl-turbo-lm06-int8 | 300 | bind | process_cold | 0 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ329PNHSS8D37588NK |
| xl-turbo-lm06-int8 | 300 | bind | warm | 1 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3VW5SMVYYFBDE5K0C |
| xl-turbo-lm06-int8 | 300 | bind | warm | 2 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3EVGMHP5MDH31C3XB |
| xl-turbo-lm06-int8 | 300 | bind | warm | 3 | not_measured | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | null | 01M4KG1EQ3N4TD5M7PR651C1F5 |

Recomendación pendiente: faltan mediciones u observaciones válidas de toda la matriz.

NVML/CUDA, sharedGPU WDDM y RAM/swap WSL son ámbitos separados; null conserva una observación ausente.

Método: wddm_auto_v3; shared_validation_level=provider_verified; shared_independent_validation=false; task_manager_contrast=conflicting_historical.
Política sellada: aef7298d66805873171cd9b771d1e27e17760ce452f8c3e710db0ab5a70083b0.
Dedicada se contrasta con NVML; shared es del proveedor agregado Windows. Sin indicio bajo esta política y cadencia no acredita ausencia causal de spill ni atribución al hijo. El viewport about:blank y la ventana visible son observaciones separadas; no acreditan la UI de M1 ni calidad musical.

Copia y repeticiones por celda (warm exige tres repeticiones válidas distintas; dispersión muestral):

| config_id | duration_s | storage | copy_s | cold_load_delta_s | break_even_cold_loads | warm_inference_median_s | warm_inference_min_s | warm_inference_max_s | warm_inference_stdev_s | warm_rtf_median | warm_rtf_stdev |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| turbo-lm06 | 30 | bind | 0 | null | null | 5.1618 | 5.0438 | 5.2894 | 0.1228 | 0.1721 | 0.0041 |
| turbo-lm06 | 30 | container_copy | null | null | null | null | null | null | null | null | null |
| turbo-lm06 | 60 | bind | null | null | null | null | null | null | null | null | null |
| turbo-lm06 | 60 | container_copy | null | null | null | null | null | null | null | null | null |
| turbo-lm06 | 180 | bind | null | null | null | null | null | null | null | null | null |
| turbo-lm06 | 180 | container_copy | null | null | null | null | null | null | null | null | null |
| turbo-lm06 | 300 | bind | null | null | null | null | null | null | null | null | null |
| turbo-lm06 | 300 | container_copy | null | null | null | null | null | null | null | null | null |
| turbo-lm17 | 30 | bind | null | null | null | null | null | null | null | null | null |
| turbo-lm17 | 30 | container_copy | null | null | null | null | null | null | null | null | null |
| turbo-lm17 | 60 | bind | null | null | null | null | null | null | null | null | null |
| turbo-lm17 | 60 | container_copy | null | null | null | null | null | null | null | null | null |
| turbo-lm17 | 180 | bind | null | null | null | null | null | null | null | null | null |
| turbo-lm17 | 180 | container_copy | null | null | null | null | null | null | null | null | null |
| turbo-lm17 | 300 | bind | null | null | null | null | null | null | null | null | null |
| turbo-lm17 | 300 | container_copy | null | null | null | null | null | null | null | null | null |
| sft-lm06 | 30 | bind | null | null | null | null | null | null | null | null | null |
| sft-lm06 | 30 | container_copy | null | null | null | null | null | null | null | null | null |
| sft-lm06 | 60 | bind | null | null | null | null | null | null | null | null | null |
| sft-lm06 | 60 | container_copy | null | null | null | null | null | null | null | null | null |
| sft-lm06 | 180 | bind | null | null | null | null | null | null | null | null | null |
| sft-lm06 | 180 | container_copy | null | null | null | null | null | null | null | null | null |
| sft-lm06 | 300 | bind | null | null | null | null | null | null | null | null | null |
| sft-lm06 | 300 | container_copy | null | null | null | null | null | null | null | null | null |
| base-lm06 | 30 | bind | null | null | null | null | null | null | null | null | null |
| base-lm06 | 30 | container_copy | null | null | null | null | null | null | null | null | null |
| base-lm06 | 60 | bind | null | null | null | null | null | null | null | null | null |
| base-lm06 | 60 | container_copy | null | null | null | null | null | null | null | null | null |
| base-lm06 | 180 | bind | null | null | null | null | null | null | null | null | null |
| base-lm06 | 180 | container_copy | null | null | null | null | null | null | null | null | null |
| base-lm06 | 300 | bind | null | null | null | null | null | null | null | null | null |
| base-lm06 | 300 | container_copy | null | null | null | null | null | null | null | null | null |
| xl-turbo-lm06-int8 | 30 | bind | null | null | null | null | null | null | null | null | null |
| xl-turbo-lm06-int8 | 30 | container_copy | null | null | null | null | null | null | null | null | null |
| xl-turbo-lm06-int8 | 60 | bind | null | null | null | null | null | null | null | null | null |
| xl-turbo-lm06-int8 | 60 | container_copy | null | null | null | null | null | null | null | null | null |
| xl-turbo-lm06-int8 | 180 | bind | null | null | null | null | null | null | null | null | null |
| xl-turbo-lm06-int8 | 180 | container_copy | null | null | null | null | null | null | null | null | null |
| xl-turbo-lm06-int8 | 300 | bind | null | null | null | null | null | null | null | null | null |
| xl-turbo-lm06-int8 | 300 | container_copy | null | null | null | null | null | null | null | null | null |

La copia se paga una vez por contenedor/grupo y no forma parte de inference_s. break_even_cold_loads = copy_s / (carga cold bind − carga cold copia), sólo para ahorro positivo; no implica control de caché.
