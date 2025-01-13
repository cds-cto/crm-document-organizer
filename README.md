# OCR Service

A powerful OCR (Optical Character Recognition) service for extracting text from images and PDF files.

## Prerequisites

### Required Software
1. [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) - OCR engine
2. [Poppler](https://poppler.freedesktop.org/) - PDF rendering library
3. [Python](https://www.python.org/downloads/) (version 3.8 or higher)
4. [pip](https://pip.pypa.io/en/stable/installation/) - Python package installer

## Installation Guide

### 1. Install Required Software

#### Windows
- Download and install Tesseract OCR from the [UB-Mannheim repository](https://github.com/UB-Mannheim/tesseract/wiki)
- Download and install Poppler from [poppler-windows](http://blog.alivate.com.au/poppler-windows/)
- Add Popper to src/poppler


## Deploy to production

- Comment the code in src/ocr_service.py: TODO: comment when deploy to production
- Run the command: `docker-compose up --build -d`

