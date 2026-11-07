# pdf_organizer (Español)

**Idiomas / Languages**: [English](README.md) · [中文](README.zh-CN.md) · [Español](README.es.md)

Organiza una carpeta de archivos PDF **por su contenido**: la herramienta extrae el
texto de las primeras páginas de cada PDF, clasifica cada documento en una categoría
temática, opcionalmente renombra los archivos cuyos nombres no tienen significado
(números, códigos, texto ilegible) con su título real, y mueve todo a subcarpetas
por categoría.

Se desarrolló y probó a fondo con un corpus mixto de 10.500 PDFs (artículos de
investigación, libros técnicos, manuales, facturas, exámenes, ficción, en
inglés/chino/danés).

## Qué hace

1. **Extraer** — de cada PDF obtiene el título de los metadatos y el texto de las
   primeras páginas (3 por defecto). Cada archivo se extrae en su propio subproceso
   con un tiempo límite estricto, de modo que un PDF dañado o cifrado no pueda
   bloquear la ejecución. Los resultados se almacenan en caché, así que repetir la
   ejecución es rápido.
2. **Clasificar** — un motor de puntuación por palabras clave evalúa cada archivo
   contra unas 55 categorías temáticas. La evidencia en el nombre del archivo y en la
   zona del título pesa más que la evidencia en el cuerpo del texto; los acrónimos
   sensibles a mayúsculas (HRTF, FIR, ADC…) se buscan de forma exacta. Los archivos
   que no coinciden con nada (o que coinciden igual con varias categorías) van a una
   carpeta `uncategorized` en lugar de adivinarse.
3. **Renombrar** (opcional) — los nombres que son puros números/códigos/ilegibilidades
   se reemplazan por el título real del documento, tomado de los metadatos o extraído
   del diseño de la primera página (líneas de titular, bloques de título en
   MAYÚSCULAS, patrones de título de arXiv/ResearchGate). Los nombres que ya tienen
   significado nunca se tocan. Los nombres de archivo en chino se reconocen como
   significativos y se conservan.
4. **Agrupar** — los archivos se mueven a una carpeta por categoría. Por defecto la
   estructura es **plana** (sin subcarpetas dentro de las carpetas de categoría).
5. **Informar** — se escriben tres informes en la carpeta de salida:
   `rename_report.txt` (nombre antiguo → nuevo), `folder_manifest.txt` (diseño final),
   `summary.txt` (recuentos por categoría).

Nunca se elimina nada. Cada movimiento se registra en `organize_log.json`, y una
ejecución puede revertirse por completo con `--undo`.

## Requisitos

- Python 3.9+
- [PyMuPDF](https://pymupdf.readthedocs.io/)

```bash
pip install -r requirements.txt
```

Documentación: **[USAGE.es.md](USAGE.es.md)** es la guía práctica paso a paso;
[README.es.md](README.es.md) (este archivo) es la referencia de opciones;
[SPECIFICATION.md](SPECIFICATION.md) contiene los detalles formales (en inglés).

Pruebas: `python tests/test_organizer.py` (autosuficiente, genera sus propios
archivos de prueba).

## Inicio rápido

```bash
# organizar una carpeta en el mismo sitio (entrada = salida), con renombrado
python pdf_organizer.py --input "E:\my_pdfs"

# ver qué PASARÍA antes — no se mueve nada
python pdf_organizer.py --input "E:\my_pdfs" --dry-run

# solo agrupar en carpetas, sin renombrar ningún archivo
python pdf_organizer.py --input "E:\my_pdfs" --no-rename

# revertir la última ejecución — el registro se encuentra automáticamente
python pdf_organizer.py --undo

# ver todas las categorías activas
python pdf_organizer.py --list-categories
```

Otras opciones de la línea de comandos: `--verbose` (recuentos de movimientos por
categoría + ejemplos de renombrado), `--version`. El proceso termina con el código 1
si algún archivo no pudo moverse.

Con un archivo de configuración (recomendado para usar todas las opciones):

```bash
cp config.example.json myconfig.json   # edítalo, y luego:
python pdf_organizer.py --config myconfig.json
```

## Opciones de configuración

| Opción (JSON) | Flag CLI | Predeterminado | Significado |
|---|---|---|---|
| `input_folder` | `--input` | `.` | Carpeta que contiene los PDF a organizar. |
| `output_folder` | `--output` | igual que la entrada | Dónde se crean las subcarpetas de categoría. **Por defecto entrada y salida son la misma carpeta**, es decir, los archivos se reorganizan en el sitio. Indica una carpeta distinta para dejar la entrada intacta. |
| `recursive` | `--recursive` | `false` | También escanea las subcarpetas de la carpeta de entrada. La carpeta de salida y la caché de extracción **nunca** se recorren, aunque estén dentro de la carpeta de entrada. |
| `ignore` | `--ignore a b …` | `[]` | Patrones glob de carpetas/archivos a omitir, p. ej. `["private", "*_backup", "invoices"]`. Coincide con cualquier segmento de ruta o con la ruta relativa. |
| `rename_files` | `--no-rename` para desactivar | `true` | Renombra los nombres sin significado al título del documento. `false` = conserva todos los nombres actuales y solo agrupa en carpetas. |
| `dry_run` | `--dry-run` | `false` | Calcula e imprime el plan completo (también se guarda en `.pdf_organizer_cache/plan_preview.txt`) sin mover nada. |
| `nested` | `--nested` | `false` | Permite subcarpetas **dentro** de las carpetas de categoría (ver `subfolder_by`). |
| `subfolder_by` | — | `"none"` | `"none"` = carpetas de categoría planas. `"first_letter"` (requiere `nested: true`) = divide cada categoría en subcarpetas `A/ … Z/`. |
| `uncategorized_folder` | — | `uncategorized` | Nombre de la carpeta para los archivos que no se pudieron clasificar. |
| `work_folder` | — | `.pdf_organizer_cache` | Directorio de caché para los resultados de extracción (permite repeticiones rápidas). |
| `workers` | `--workers N` | `8` | Subprocesos de extracción en paralelo. |
| `extract_timeout_sec` | — | `45` | Tiempo límite estricto por PDF durante la extracción. |
| `max_pages` | — | `3` | Páginas de texto extraídas por PDF. |
| `log_file` | — | `organize_log.json` | Registro de reversión escrito en la carpeta de salida (`null` para desactivarlo). |
| `reports.enabled` | — | `true` | Escribe los tres archivos de informe. |
| `reports.rename_report` / `reports.manifest` / `reports.summary` | — | `rename_report.txt` / `folder_manifest.txt` / `summary.txt` | Nombres de los informes (relativos a la carpeta de salida). |
| `classifier.min_score` | — | `2.0` | Puntuación mínima de evidencia para aceptar una categoría. |
| `classifier.min_margin` | — | `0.5` | Diferencia exigida entre la mejor y la segunda mejor categoría; menor = más decidido, mayor = más archivos quedan sin categorizar. |
| `classifier.custom_categories` | — | `[]` | Tus propias categorías, evaluadas **antes** que las integradas. Ejemplo abajo. |
| `classifier.disable_categories` | — | `[]` | Nombres de categorías integradas a desactivar (sus archivos pasan a otras categorías o a `uncategorized`). |

## Ejemplos

### 1. Reorganizar en el sitio (para lo que se creó esta herramienta)

```json
{
  "input_folder": "E:\\pdf_regroup",
  "output_folder": "E:\\pdf_regroup",
  "rename_files": true
}
```

Entrada y salida son la misma carpeta: el montón plano de PDFs se convierte en un
conjunto de carpetas temáticas, y los archivos mal nombrados obtienen sus títulos
reales.

### 2. Carpeta de salida aparte, conservar los nombres, ignorar algunas carpetas

```json
{
  "input_folder": "C:\\Users\\me\\Downloads",
  "output_folder": "D:\\library",
  "rename_files": false,
  "recursive": true,
  "ignore": ["*.tmp", "family_photos", "invoices_*"]
}
```

Lee los PDF de Downloads **y de sus subcarpetas**, omite todo lo que coincida con los
patrones de ignore, ordena copias en `D:\library\<category>\` sin renombrar, y deja
la carpeta Downloads intacta.

### 3. Colecciones grandes: subcarpetas anidadas por inicial

```json
{
  "input_folder": "E:\\papers",
  "nested": true,
  "subfolder_by": "first_letter"
}
```

Genera `E:\papers\noise_reduction\A\`, `…\B\`, … de modo que ninguna carpeta suelta
contenga miles de archivos.

### 4. Categorías personalizadas

```json
{
  "input_folder": "E:\\work_docs",
  "classifier": {
    "custom_categories": [
      { "name": "company_reports",
        "keywords": ["acme corp", "quarterly report", "ACME-202"],
        "weak_keywords": ["acme"] }
    ]
  }
}
```

Los archivos que mencionen "acme corp", etc., van a una carpeta `company_reports`
antes de que siquiera se consideren las categorías integradas.

### 5. Primero dry-run (recomendado)

```bash
python pdf_organizer.py --input "E:\my_pdfs" --dry-run
# revisa .pdf_organizer_cache/plan_preview.txt, y luego:
python pdf_organizer.py --input "E:\my_pdfs"
```

### 6. Revertir una ejecución

```bash
python pdf_organizer.py --undo              # encuentra organize_log.json automáticamente
# o de forma explícita:
python pdf_organizer.py --undo "E:\my_pdfs\organize_log.json"
```

Devuelve cada archivo a su ruta original y elimina las carpetas que creó la ejecución.

## El esquema de categorías

Las reglas por defecto codifican un estándar de clasificación de conocimiento de
propósito general, derivado de — y probado a fondo con — la biblioteca mixta real
de 10.500 PDFs mencionada arriba (artículos de investigación, manuales técnicos,
documentos administrativos personales, facturas, ficción; inglés/chino/danés).
Abarca áreas temáticas como el procesamiento de audio y voz, DSP y matemáticas,
programación e informática, administración personal (facturas, banca/impuestos,
reservas de viaje, certificados) y material de lectura general.

No necesitas la lista completa de antemano:

- Consulta todas las categorías activas en cualquier momento con `--list-categories`.
- El esquema completo vive en un único archivo, `organizer/rules.py`, por si
  quieres modificarlo.
- Añade tus propios temas o desactiva los integrados con
  `classifier.custom_categories` / `classifier.disable_categories` (ver arriba).
- Los informes y `--list-categories` anotan cada categoría con su clase superior
  de la **Library of Congress Classification** y su área temática de **arXiv** —
  el esquema de la herramienta se mantiene relacionable con las clasificaciones
  estándar del conocimiento humano (`organizer/schemes.py`). Los documentos
  personales/prácticos (facturas, certificados, reservas) no tienen clase en
  ningún esquema bibliotecario o científico y quedan en blanco.

## Notas y limitaciones

- La clasificación se basa en evidencia de palabras clave: es rápida y totalmente
  offline, pero un documento cuyas primeras páginas no contienen palabras clave
  reconocibles del tema acabará en `uncategorized` (ajusta `min_score` /
  `min_margin`, o añade una categoría personalizada).
- Los PDF escaneados/solo imagen no tienen texto extraíble; se agrupan solo por la
  evidencia del nombre del archivo.
- Los PDF dañados o protegidos con contraseña igualmente se mueven (a
  `uncategorized`) pero no pueden renombrarse a partir del contenido.
- Los movimientos dentro de la misma unidad son instantáneos; entre unidades
  distintas los archivos se copian y luego se eliminan.
- La caché de extracción (`.pdf_organizer_cache/`) puede borrarse sin peligro; se
  reconstruirá en la siguiente ejecución.

## Estructura

```
pdf_organizer/
├── pdf_organizer.py        # punto de entrada de la CLI
├── config.example.json     # configuración por defecto documentada
├── requirements.txt
├── USAGE.md                # guía de uso práctica paso a paso (inglés)
├── USAGE.es.md             # guía de uso práctica (español)
├── SPECIFICATION.md        # especificación de software (inglés)
├── tests/
│   └── test_organizer.py   # programa de pruebas autosuficiente
└── organizer/
    ├── config.py           # carga/validación de la configuración
    ├── rules.py            # esquema de categorías integradas
    ├── extract.py          # controlador de extracción paralelo con tiempos límite
    ├── _extract_worker.py  # subproceso de extracción por PDF
    ├── classify.py         # clasificador por puntuación
    ├── rename.py           # detección de nombres sin sentido + extracción de título
    ├── schemes.py          # códigos de clasificación estándar LCC / arXiv
    ├── executor.py         # plan/aplicar/deshacer
    └── report.py           # los tres archivos de informe
```
