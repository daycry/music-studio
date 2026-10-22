# Testigo funcional nativo de acceso mínimo y flush — T05

ROOT 2026-10-11T15:56:18.283475+00:00: verificados45payload,13fuentes/13snapshot,3testigosfuncionales/3controlesUUID independientes. Access0x00120083 sinAPPEND/GENERIC_WRITE,share0,options0x0020006a,FileMode0x2a,B65536. Cadaarchivo131072B:doswritesNTexactos,FlushFileBuffers sobremismohandle,dosreadsNTexactos/patronesSHAidénticos/IDestable/EOFactual. FILE_CREATE relativoNOREPLACE,Information2; noampliaciónderechos ni producción.

**Exits originales1 conservados:** los3procesos terminan concontador global134→135. Todos10handles propiosporproceso cerrados y1arena liberada; recursospropiospendientes0. ControlUUIDen3procesos sinarchivosobserva deltas1/0/0, coherentecon deriva inicial; noidentifica handleinterno ni demuestraausenciauniversaldefugas. No se sustituyen exits ni se presenta la suiteexperimental como completamenteverde.

ROOTreleefilespropios/comparahashesde2bloques,verifica rawNTstatus/IOSB.Information/modos/alineación/crear/write/flush/read/close/free yPIDspropiosactuales0. Fixturesconservados3×131072B. Fuente: namespaceprivado .cache/dev-cycle/m1/storage-journal-store-flush-probe-20261011,payload-manifest-final.json,supervisor-result.json,3native-result yuuid-control-result.json. Herramientasfijadas/streams/argvUTC/reaps, originalesintactos.

Esto respondeúnicamentelagatedefuncionalidaddeWRITE_DATAsinAPPEND yFlushFileBuffers delcontratoADR0081. No acreditaS1full,writerautoridad,ACKdurable,powerloss,storeproducto,bootstrap,lifecycle,recoverycausal,ext4/E2E/manuales,T05niM1. TDD n/a: verificaciónnativa experimental, ningúncomportamientoproductoimplementado. Kernel/storeproductorequieresupropiodesarrolloconTDD/revisión/QA.
