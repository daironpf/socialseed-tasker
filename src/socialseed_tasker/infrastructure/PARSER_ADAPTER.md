Parser Adapter (TreeSitterParser)

Purpose
- Provide a deterministic ParserPort implementation.
- Use Tree-Sitter when available for richer multi-language parsing.
- Fall back to Python's builtin ast for .py files when Tree-Sitter is not available.

Behavior and return shapes
- parse_file(path) -> dict with keys: type, start_byte/end_byte or location, text, children (list).
- extract_symbols(ast_dict) -> list of dicts: {name, type, location}.
- extract_imports(ast_dict) -> list[str] of import targets.

Configuration
- TASKER_PARSER_EXTENSIONS: comma-separated extensions (default ".py")
- TASKER_TREESITTER_PYTHON_SO: optional path to compiled Tree-Sitter python language .so file

Fallback semantics
- If Tree-Sitter is available and a compiled grammar path is provided, Tree-Sitter is used for .py files.
- If Tree-Sitter is not available or initialization fails, the adapter uses Python ast for .py files.
- For non-.py extensions, Tree-Sitter is required; otherwise parse_file raises ParserError.

Examples
- Python fallback:
  parser = TreeSitterParser()
  ast = parser.parse_file("project/module.py")
  symbols = parser.extract_symbols(ast)
  imports = parser.extract_imports(ast)
