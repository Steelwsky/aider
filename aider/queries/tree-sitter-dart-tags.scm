(class_definition
  name: (identifier) @name.definition.class) @definition.class

(constructor_signature
  name: (identifier) @name.definition.type)

(function_signature
  name: (identifier) @name.definition.function) @definition.function

(scoped_identifier
  scope: (identifier) @name.reference.namespace)

(getter_signature
  (identifier) @name.reference.function)

(setter_signature
  name: (identifier) @name.reference.function)

(inferred_type) @keyword