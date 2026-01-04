unknown:
	@echo Unknown action. Exiting

.PHONY: stub
stub:
	@uv run ftl stub ./locales/ ./app/_stub.pyi