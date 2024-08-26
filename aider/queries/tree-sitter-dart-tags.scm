; Class definitions
(class_definition
  name: (identifier) @name.definition.class) @definition.class

; Constructor definitions
(constructor_signature
  name: (identifier) @name.definition.constructor) @definition.constructor

; Method definitions
(method_signature
  name: (identifier) @name.definition.method) @definition.method

; Function definitions
(function_signature
  name: (identifier) @name.definition.function) @definition.function

; Getter definitions
(getter_signature
  (identifier) @name.definition.getter) @definition.getter

; Setter definitions
(setter_signature
  name: (identifier) @name.definition.setter) @definition.setter

; Function/method calls
(function_expression_invocation
  function: (identifier) @name.reference.call) @reference.call

(method_invocation
  name: (identifier) @name.reference.call) @reference.call

; Class instantiation
(instance_creation_expression
  type: (type_identifier) @name.reference.class) @reference.class

; Type references
(type_identifier) @name.reference.type

; Built-in types
((type_identifier) @name.reference.type.builtin
  (#match? @name.reference.type.builtin "^(int|double|String|bool|List|Set|Map|Runes|Symbol)$"))

; Scoped identifiers (for namespaces or static members)
(scoped_identifier
  scope: (identifier) @name.reference.namespace
  name: (identifier) @name.reference.member)

; Scoped type identifiers
((scoped_identifier
  scope: (identifier) @name.reference.type
  name: (identifier) @name.reference.type)
  (#match? @name.reference.type "^[A-Z]"))
