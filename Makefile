# run on git bash
PYINSTALLER = pyinstaller
MAIN_SCRIPT = ./src/main.py
ICON = ./assets/icons/explorer.ico

ADD_DATA = \
    --add-data "./assets/data/mimetype.json;assets/data" \
    --add-data "./assets/icons/safe.ico;assets/icons" \
    --add-data "./assets/icons/unsafe.ico;assets/icons" \
    --add-data "./assets/icons/explorer.ico;assets/icons"

build:
	$(PYINSTALLER) --noconsole --onefile $(MAIN_SCRIPT) $(ADD_DATA) --icon=$(ICON)

clean:
	rm -rf build dist __pycache__
	rm -f *.spec

.PHONY: build clean
