all: tools

tools:
	@ (cd tools ; ./compile_tools.sh)

.PHONY: all tools
