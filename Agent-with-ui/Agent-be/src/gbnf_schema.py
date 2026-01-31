# strict_grammar.py

GBNF_SCHEMA = r"""
# --- ROOT RULE (Modified to allow Thinking) ---
root ::= (thought-block ws)? "[" ws item-list "]"

# --- THINKING BLOCK ---
# We allow "<think>", then any text (excluding '<' to avoid ambiguity), then "</think>"
# This effectively forces the model to finish thinking before starting the JSON.
thought-block ::= "<think>" thought-content "</think>"
thought-content ::= [^<]+ 

# --- JSON LIST ---
item-list ::= item | item "," ws item-list

# Consolidated item rule
item ::= delete-op | update-string-field | update-chat-history | update-prev-actions | update-rough-plan | update-variables | update-env-state | update-episodic-desc | update-things-to-note | update-current-func

# --- 1. Delete Operation ---
delete-op ::= "{" ws "\"type\"" ws ":" ws "\"delete\"" "," ws "\"field\"" ws ":" ws field-enum "," ws "\"serial_number\"" ws ":" ws number "}"

# --- 2. String Field Updates ---
update-string-field ::= "{" ws "\"type\"" ws ":" ws add-or-update "," ws "\"field\"" ws ":" ws string-field-enum "," ws "\"serial_number\"" ws ":" ws number "," ws "\"updated\"" ws ":" ws string "}"

# --- 3. Complex Object Updates ---
update-chat-history ::= "{" ws "\"type\"" ws ":" ws add-or-update "," ws "\"field\"" ws ":" ws "\"chat_history\"" "," ws "\"serial_number\"" ws ":" ws number "," ws "\"updated\"" ws ":" ws chat-obj "}"

update-prev-actions ::= "{" ws "\"type\"" ws ":" ws add-or-update "," ws "\"field\"" ws ":" ws "\"previous_actions_and_logs\"" "," ws "\"serial_number\"" ws ":" ws number "," ws "\"updated\"" ws ":" ws prev-action-obj "}"

update-rough-plan ::= "{" ws "\"type\"" ws ":" ws add-or-update "," ws "\"field\"" ws ":" ws "\"rough_plan_to_reach_goal\"" "," ws "\"serial_number\"" ws ":" ws number "," ws "\"updated\"" ws ":" ws plan-obj "}"

update-variables ::= "{" ws "\"type\"" ws ":" ws add-or-update "," ws "\"field\"" ws ":" ws "\"variables\"" "," ws "\"serial_number\"" ws ":" ws number "," ws "\"updated\"" ws ":" ws variable-obj "}"

update-env-state ::= "{" ws "\"type\"" ws ":" ws add-or-update "," ws "\"field\"" ws ":" ws "\"env_state\"" "," ws "\"serial_number\"" ws ":" ws number "," ws "\"updated\"" ws ":" ws env-state-obj "}"

update-episodic-desc ::= "{" ws "\"type\"" ws ":" ws add-or-update "," ws "\"field\"" ws ":" ws "\"episodic_memory_descriptions\"" "," ws "\"serial_number\"" ws ":" ws number "," ws "\"updated\"" ws ":" ws episodic-obj "}"

update-things-to-note ::= "{" ws "\"type\"" ws ":" ws add-or-update "," ws "\"field\"" ws ":" ws "\"things_to_note\"" "," ws "\"serial_number\"" ws ":" ws number "," ws "\"updated\"" ws ":" ws note-obj "}"

update-current-func ::= "{" ws "\"type\"" ws ":" ws add-or-update "," ws "\"field\"" ws ":" ws "\"current_function_to_execute\"" "," ws "\"serial_number\"" ws ":" ws number "," ws "\"updated\"" ws ":" ws func-obj "}"

# --- Inner Objects ---
chat-obj ::= "{" ws "\"serial_number\"" ws ":" ws number "," ws "\"role\"" ws ":" ws string "," ws "\"content\"" ws ":" ws string "}"

prev-action-obj ::= "{" ws "\"serial_number\"" ws ":" ws number "," ws "\"description\"" ws ":" ws string "," ws "\"function_name\"" ws ":" ws string "," ws "\"inputs\"" ws ":" ws json-dict "," ws "\"outputs\"" ws ":" ws json-dict "," ws "\"log\"" ws ":" ws string "," ws "\"filter_words\"" ws ":" ws string-list "}"

plan-obj ::= "{" ws "\"serial_number\"" ws ":" ws number "," ws "\"description\"" ws ":" ws string "," ws "\"function_name\"" ws ":" ws string "," ws "\"inputs\"" ws ":" ws json-dict "," ws "\"brief_expected_outputs\"" ws ":" ws string-list "," ws "\"status\"" ws ":" ws string "}"

variable-obj ::= "{" ws "\"serial_number\"" ws ":" ws number "," ws "\"variable_type\"" ws ":" ws string "," ws "\"description\"" ws ":" ws string "," ws "\"content\"" ws ":" ws string "," ws "\"filter_words\"" ws ":" ws string-list "}"

env-state-obj ::= "{" ws "\"serial_number\"" ws ":" ws number "," ws "\"description\"" ws ":" ws string "," ws "\"content\"" ws ":" ws string "}"

episodic-obj ::= "{" ws "\"serial_number\"" ws ":" ws number "," ws "\"description\"" ws ":" ws string "}"

note-obj ::= "{" ws "\"serial_number\"" ws ":" ws number "," ws "\"description\"" ws ":" ws string "," ws "\"content\"" ws ":" ws string "}"

func-obj ::= "{" ws "\"function_name\"" ws ":" ws string "," ws "\"inputs\"" ws ":" ws json-dict "}"

# --- Enums and Primitives ---
add-or-update ::= "\"add\"" | "\"update\""

string-field-enum ::= "\"satisfied\"" | "\"final_goal\"" | "\"current_goal\"" | "\"final_goal_completed\""

field-enum ::= string-field-enum | "\"chat_history\"" | "\"previous_actions_and_logs\"" | "\"rough_plan_to_reach_goal\"" | "\"variables\"" | "\"env_state\"" | "\"episodic_memory_descriptions\"" | "\"things_to_note\"" | "\"current_function_to_execute\""

string ::= "\"" ( [^"\\\x7F\x00-\x1F] | "\\" (["\\/bfnrt] | "u" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F]) )* "\""
number ::= "-"? ("0" | [1-9] [0-9]*) ("." [0-9]+)? ([eE] [-+]? [0-9]+)?
ws ::= [ \t\n\r]*

# Recursive structures
json-val ::= string | number | "true" | "false" | "null" | json-dict | json-list
json-dict ::= "{" ws (string ws ":" ws json-val ("," ws string ws ":" ws json-val)*)? ws "}"
json-list ::= "[" ws (json-val ("," ws json-val)*)? ws "]"
string-list ::= "[" ws (string ("," ws string)*)? ws "]"
"""