# Minimal makefile for Sphinx documentation

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Install documentation dependencies
install:
	pip install -r requirements.txt

# Clean build directory
clean:
	rm -rf $(BUILDDIR)/*

# Build HTML documentation
html:
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

# Build HTML documentation with auto-reload for development
livehtml:
	sphinx-autobuild -b html $(SOURCEDIR) $(BUILDDIR)/html --port 8000

# Build LaTeX/PDF documentation
latexpdf:
	@$(SPHINXBUILD) -M latexpdf "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo
	@echo "Build finished. The PDF is in $(BUILDDIR)/latex."

# Build EPUB documentation
epub:
	@$(SPHINXBUILD) -M epub "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo
	@echo "Build finished. The EPUB file is in $(BUILDDIR)/epub."

# Check for broken links
linkcheck:
	@$(SPHINXBUILD) -M linkcheck "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo
	@echo "Link check complete. Results in $(BUILDDIR)/linkcheck."

# Check documentation coverage
coverage:
	@$(SPHINXBUILD) -M coverage "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo
	@echo "Coverage check complete. Results in $(BUILDDIR)/coverage."

# Generate API documentation from docstrings
apidoc:
	sphinx-apidoc -f -o $(SOURCEDIR)/api ../src

# Full build: clean, generate API docs, and build HTML
full: clean apidoc html

# Deploy to GitHub Pages
deploy:
	@echo "Deploying to GitHub Pages..."
	ghp-import -n -p -f $(BUILDDIR)/html

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
