

unknown:
	@echo Unknown action. Exiting

.PHONY: stub
stub:
	@uv run ftl stub locales .

.PHONY: run
run:
	uv run -m app