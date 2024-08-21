; Keywords
(keyword) @keyword

; Functions
(function_signature
  name: (identifier) @function)
(function_invocation
  function: (identifier) @function.call)

; Types
(type_identifier) @type
(type_alias
  (type_identifier) @type.definition)

; Variables
(variable_declaration
  name: (identifier) @variable)

; Constants
(const_declaration
  name: (identifier) @constant)

; Strings
(string_literal) @string

; Numbers
(integer_literal) @number
(double_literal) @number

; Comments
(comment) @comment
(documentation_comment) @comment.documentation

; Operators
[
  "+"
  "-"
  "*"
  "/"
  "%"
  "=="
  "!="
  ">"
  "<"
  ">="
  "<="
  "&&"
  "||"
  "!"
  "??"
] @operator

; Punctuation
[
  "("
  ")"
  "["
  "]"
  "{"
  "}"
  ";"
  ","
  "."
] @punctuation.delimiter

; Classes
(class_definition
  name: (identifier) @type)

; Methods
(method_signature
  name: (identifier) @method)

; Constructors
(constructor_signature
  name: (identifier) @constructor)

; Annotations
(annotation
  name: (identifier) @attribute)

; Imports
(import_specification
  path: (string_literal) @string.special)

; Null
(null_literal) @constant.builtin

; Boolean
(boolean_literal) @boolean

; This
(this) @variable.builtin
