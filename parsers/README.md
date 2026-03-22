Этот каталог содержит автоматически сгенерированные шаблоны парсеров и файл parsers.json,
содержащий рекомендованные конфигурации для каждого PDF из manifest.txt.

Как использовать:
1) Установите зависимости:
   pip install requests PyMuPDF pdfplumber
   (опционально: pytesseract, camelot-py[cv])
2) Запустите скрипт:
   python scripts/analyze_and_generate_parsers.py --manifest-url <URL>
3) Скрипт скачает PDF в ./_downloaded_pdfs, выполнит анализ и создаст:
   - parsers/parsers.json
   - parsers/<safe_name>_parser.py (стаб-обработчик для дальнейшей реализации)

Дальнейшие шаги:
- Открыть парсер-стаб и реализовать парсинг карточек/таблиц для конкретного PDF.
- При необходимости добавить ручную разметку для шаблонов с нестандартной вёрсткой.
