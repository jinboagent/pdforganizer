# pdf_organizer — Guía de uso (Español)

**Idiomas / Languages**: [English](USAGE.md) · [中文](USAGE.zh-CN.md) · [Español](USAGE.es.md)

Compañera práctica, paso a paso, del [README](README.es.md) (referencia) y de
[SPECIFICATION](SPECIFICATION.md) (detalles formales, en inglés). Esta página trata
de *cómo se maneja la herramienta en el día a día*.

---

## 1. Qué hace, en una frase

La apuntas a una carpeta de PDFs. Lee las primeras páginas de cada archivo, averigua
de qué trata cada documento, da a los archivos sin nombre (`12345.pdf`,
`scan_final.pdf`, texto ilegible) sus títulos reales, y ordena todo en carpetas
temáticas como `noise_reduction/`, `programming_python/`, `bills_utilities/`. No se
borra nada, cada movimiento queda registrado y toda la ejecución puede deshacerse.

## 2. Empezar en 5 minutos

```bash
pip install pymupdf

# paso 1 — mira antes de saltar (no se mueve nada):
python pdf_organizer.py --input "D:\Messy PDFs" --dry-run

# paso 2 — lee el plan que imprimió (también se guarda en .pdf_organizer_cache/plan_preview.txt)

# paso 3 — hazlo de verdad:
python pdf_organizer.py --input "D:\Messy PDFs"

# paso 4 — ¿te arrepientes? un comando lo devuelve todo:
python pdf_organizer.py --undo
```

Ese es el ciclo completo. El resto de esta guía trata de hacerlo *bien*.

## 3. El flujo de trabajo seguro recomendado

Para una primera ejecución sobre una carpeta importante:

1. **Copia, no arriesgues.** O ejecutas con una carpeta de salida aparte
   (`--input EN --output FUERA` deja la carpeta de entrada intacta), o haces una
   copia de seguridad. O confías en `--undo` — es exacto y está probado, pero las
   copias de seguridad cuestan menos que los arrepentimientos.
2. **Primero dry-run.** Revisa la tabla de categorías. Es normal que haya *algunos*
   archivos en `uncategorized` — eso es la herramienta siendo honesta, no rota (ver §7).
3. **Ejecuta de verdad.** Anota la ruta de `Undo log:` que se imprime.
4. **Inspecciona los resultados** en `rename_report.txt` (nombres antiguos → nuevos)
   y `folder_manifest.txt` (dónde acabó cada cosa).
5. **Itera.** ¿Archivos en la categoría equivocada? Añade una categoría personalizada
   o ajusta los umbrales (§6) y vuelve a ejecutar — la caché de extracción hace que
   repetir sea rápido, y la segunda vez solo se mueven los archivos *mal ubicados*.

## 4. Escenarios cotidianos

### "Mis PDFs son un montón plano enorme — organízalos en el sitio"

```bash
python pdf_organizer.py --input "E:\papers" --dry-run
python pdf_organizer.py --input "E:\papers"
```

Entrada y salida son la misma carpeta por defecto: el montón se convierte en carpetas
temáticas y los nombres malos se convierten en títulos reales.

### "Ordena copias en una carpeta de biblioteca, conserva mis originales y sus nombres"

```bash
python pdf_organizer.py --input "C:\Users\me\Downloads" --output "D:\library" --no-rename --recursive
```

### "Mi carpeta de descargas tiene cosas que nunca quiero que se toquen"

```bash
python pdf_organizer.py --input "D:\In" --output "D:\Out" --recursive --ignore private receipts_*
```

(O pon los mismos patrones en `config.json` bajo `"ignore"`.)

### "Tengo 20.000 PDFs y las carpetas serían inmanejables"

```bash
python pdf_organizer.py --input "E:\big" --nested
```

Cada carpeta de categoría se divide por inicial: `noise_reduction/A/`,
`noise_reduction/B/`…

### "Mi campo tiene temas que la herramienta no conoce"

```json
{
  "input_folder": "E:\\thesis_chapters",
  "classifier": {
    "custom_categories": [
      { "name": "bicycle_dynamics",
        "keywords": ["bicycle dynamics", "wheel gyroscopic"],
        "weak_keywords": ["bicycle"] }
    ],
    "disable_categories": ["danish_education"]
  }
}
```

```bash
python pdf_organizer.py --config myconfig.json
```

Las categorías personalizadas ganan los empates contra las integradas. Mira todas
las activas con:

```bash
python pdf_organizer.py --list-categories
```

### "Sigo añadiendo PDFs a la carpeta"

Simplemente vuelve a ejecutar el mismo comando. La extracción está en caché, así que
solo se leen los archivos nuevos, y solo *ellos* se mueven. La herramienta además
nunca rebaraja sus propios resultados — los escaneos recursivos saltan
automáticamente la carpeta de salida y la caché.

### "Solo quiero el renombrado, no las carpetas" (o al revés)

- Renombrar dejando todo en un solo lugar: no es trabajo para esta herramienta
  (siempre agrupa).
- Agrupar sin renombrar: `--no-rename`.

## 5. Leer la salida

| Archivo | Qué te dice |
|---|---|
| consola | El plan de categorías antes de la ejecución; recuentos de movimientos/errores después |
| `rename_report.txt` | Cada archivo renombrado: nombre antiguo → nuevo, agrupado por carpeta |
| `folder_manifest.txt` | El diseño final completo — dónde acabó cada PDF |
| `summary.txt` | Recuentos por categoría |
| `organize_log.json` | Registro de movimientos legible por máquina (lo usa `--undo`) |
| `.pdf_organizer_cache/` | Caché de extracción + `plan_preview.txt` de los dry-runs. Seguro de borrar. |

## 6. Ajustar el clasificador

- **¿Demasiados archivos en `uncategorized`?** Baja el listón de evidencia:
  `"classifier": { "min_score": 1.5, "min_margin": 0.3 }`. O añade categorías
  personalizadas para tus temas. O sube `max_pages` (3 por defecto) para que se lea
  más texto.
- **¿Archivos que caen en la categoría equivocada?** Sube `min_margin` (p. ej.
  `1.0`) para que solo se asignen victorias claras, y comprueba en
  `folder_manifest.txt` qué categoría los está "robando"; añade una categoría
  personalizada más específica — las personalizadas se comprueban antes que las
  integradas.
- **¿Una categoría que nunca necesitas está capturando archivos?** Desactívala:
  `"classifier": { "disable_categories": ["fiction"] }`.

## 7. Resolución de problemas

| Síntoma | Explicación y solución |
|---|---|
| Muchos archivos en `uncategorized/` | Los PDF escaneados/solo imagen no tienen texto que leer (sin OCR); o las primeras páginas carecen de palabras clave del tema. Ver §6. |
| Un archivo no se renombró | Su nombre ya se consideró significativo, o no se halló un título fiable en el texto. Renómbralo a mano — la herramienta nunca toca nombres de los que no está segura. |
| Un archivo tipo `broken.pdf` acabó en `uncategorized/` | Dañado o protegido con contraseña; igualmente se movió, pero no se puede leer. Arregla el archivo y vuelve a ejecutar. |
| Errores de "archivo en uso" en Windows | Un visor tiene el archivo abierto. Ciérralo y vuelve a ejecutar — la caché de extracción hace que reintentar sea barato. |
| Volví a ejecutar y no pasó nada | Todo ya estaba ordenado; el plan está vacío. Eso es éxito, no fracaso. |
| Al deshacer dice "No organize_log.json found" | Pasa la ruta explícitamente: `--undo "D:\Out\organize_log.json"` — el registro vive en la carpeta de **salida** de la ejecución. |

## 8. Buenas costumbres

- Una carpeta, un propósito: no apuntes `--recursive` a una carpeta de propósito
  general (como todo tu perfil de usuario) — organizarás cosas que no querías.
- Prefiere un archivo de configuración a líneas de comandos largas; guarda uno por
  proyecto (`python pdf_organizer.py --config library.json`).
- Vuelve a ejecutar tras añadir muchos archivos en lugar de acumular: las
  ejecuciones incrementales son baratas gracias a la caché.
- Uso en scripts/CI: el proceso termina con código 1 si algún archivo no pudo
  moverse, así que los fallos se detectan sin parsear la salida. Usa `--verbose`
  para detalle por categoría en los registros.

## 9. Para ir más a fondo

- [README.es.md](README.es.md) — referencia completa de opciones y lista de categorías integradas
- [SPECIFICATION.md](SPECIFICATION.md) — cómo puntúa el clasificador, formatos de datos, garantías (inglés)
- `organizer/rules.py` — los patrones de las categorías, si quieres retocar el esquema
