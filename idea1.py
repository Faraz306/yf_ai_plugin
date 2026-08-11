import flet as ft
import os
import json
import re
import sys
import subprocess
from pathlib import Path

import scrubadub
import git
from groq import Groq
from pydantic import TypeAdapter


# ============================================================
# CONFIGURATION
# ============================================================

CHAT_FILE = "chat_history.json"

client = Groq(api_key="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")

StringSchema = TypeAdapter(str)


# ============================================================
# CHAT HISTORY
# ============================================================

def load_chat_history():
    if not os.path.exists(CHAT_FILE):
        return []

    try:
        with open(
            CHAT_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return []


def save_chat_history(history):
    with open(
        CHAT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            history,
            file,
            indent=4,
            ensure_ascii=False
        )


def read_history():
    if not os.path.exists(CHAT_FILE):
        return "No history found."

    try:
        with open(
            CHAT_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return file.read()

    except OSError:
        return "Unable to read history."


# ============================================================
# WORKSPACE DISCOVERY
# ============================================================

def discover_dir(current_dir: Path) -> Path:

    current_dir = current_dir.resolve()

    anchors = [
        ".git",
        "pyproject.toml",
        "package.json",
        "config.json",
        "chat_history.json",
    ]

    for anchor in anchors:

        if (current_dir / anchor).exists():
            return current_dir

    if current_dir.parent == current_dir:
        return Path.cwd().resolve()

    return discover_dir(current_dir.parent)


WORKSPACE_ROOT = discover_dir(Path.cwd())


# ============================================================
# SAFE PATH HANDLING
# ============================================================

def safe_workspace_path(file_name: str) -> Path:

    if not file_name:
        raise ValueError(
            "File name cannot be empty."
        )

    requested = Path(file_name)

    if requested.is_absolute():
        raise ValueError(
            "Absolute paths are not allowed."
        )

    target = (
        WORKSPACE_ROOT / requested
    ).resolve()

    try:

        target.relative_to(
            WORKSPACE_ROOT
        )

    except ValueError:

        raise ValueError(
            "Path escapes the workspace."
        )

    return target


# ============================================================
# FILE OPERATIONS
# ============================================================

def create_or_replace_file(
    file_name: str,
    code: str
):

    target = safe_workspace_path(
        file_name
    )

    target.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    existed = target.exists()

    target.write_text(
        code.rstrip() + "\n",
        encoding="utf-8"
    )

    relative = target.relative_to(
        WORKSPACE_ROOT
    )

    if existed:
        return (
            f"File successfully replaced: "
            f"{relative}"
        )

    return (
        f"File successfully created: "
        f"{relative}"
    )


def read_file(file_name: str):

    target = safe_workspace_path(
        file_name
    )

    if not target.exists():
        return (
            f"File does not exist: "
            f"{file_name}"
        )

    try:

        return target.read_text(
            encoding="utf-8"
        )

    except Exception as error:

        return (
            f"Unable to read {file_name}: "
            f"{error}"
        )


def edit_file(
    file_name: str,
    code: str
):

    target = safe_workspace_path(
        file_name
    )

    if not target.exists():
        return (
            f"Error: File does not exist: "
            f"{file_name}"
        )

    target.write_text(
        code.rstrip() + "\n",
        encoding="utf-8"
    )

    return (
        f"Successfully updated "
        f"{target.relative_to(WORKSPACE_ROOT)}"
    )


def delete_file(file_name: str):

    target = safe_workspace_path(
        file_name
    )

    if not target.exists():
        return (
            f"Error: File does not exist: "
            f"{file_name}"
        )

    target.unlink()

    return (
        f"Successfully deleted "
        f"{target.relative_to(WORKSPACE_ROOT)}"
    )


def file_exists(file_name: str):

    target = safe_workspace_path(
        file_name
    )

    return target.exists()


# ============================================================
# PYTHON VALIDATION
# ============================================================

def validate_python_file(
    file_name: str
):

    target = safe_workspace_path(
        file_name
    )

    if not target.exists():
        return (
            "VALIDATION FAILED: "
            f"{file_name} does not exist."
        )

    if target.suffix.lower() != ".py":
        return (
            "VALIDATION SKIPPED: "
            "file is not a Python file."
        )

    try:

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "py_compile",
                str(target)
            ],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:

            return (
                f"VALIDATION PASSED: "
                f"{file_name} contains valid Python syntax."
            )

        return (
            f"VALIDATION FAILED: "
            f"{file_name}\n"
            f"{result.stderr.strip()}"
        )

    except subprocess.TimeoutExpired:

        return (
            "VALIDATION FAILED: "
            "Python syntax validation timed out."
        )

    except Exception as error:

        return (
            f"VALIDATION FAILED: {error}"
        )


# ============================================================
# PACKAGE INSTALLATION
# ============================================================

def install_library(
    library_name: str
):

    if not library_name:
        return (
            "Installation failed: "
            "library name is empty."
        )

    try:

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                library_name
            ],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:

            return (
                f"Successfully installed "
                f"{library_name}.\n\n"
                f"{result.stdout.strip()}"
            )

        return (
            f"Failed to install "
            f"{library_name}.\n\n"
            f"{result.stderr.strip()}"
        )

    except subprocess.TimeoutExpired:

        return (
            f"Installation timed out: "
            f"{library_name}"
        )

    except Exception as error:

        return (
            f"Installation error: {error}"
        )


# ============================================================
# SHELL
# ============================================================

FORBIDDEN_COMMANDS = [
    "rm -rf",
    "rm -fr",
    "del /f",
    "del /s",
    "format ",
    "mkfs",
    "shred",
]


def ask_for_command_and_execute_command(
    command: str
):

    if not command:
        return "Error: command is empty."

    normalized = command.lower().strip()

    for forbidden in FORBIDDEN_COMMANDS:

        if forbidden in normalized:

            return (
                "Execution blocked. "
                f"High-risk command detected: "
                f"{forbidden}"
            )

    try:

        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        output_parts = []

        if stdout:
            output_parts.append(
                "STDOUT:\n" + stdout
            )

        if stderr:
            output_parts.append(
                "STDERR:\n" + stderr
            )

        if not output_parts:

            output_parts.append(
                "Command completed with no output."
            )

        output_parts.append(
            f"Exit code: {result.returncode}"
        )

        return "\n\n".join(
            output_parts
        )

    except subprocess.TimeoutExpired:

        return (
            "Command timed out after "
            "30 seconds."
        )

    except Exception as error:

        return (
            f"Execution error: {error}"
        )


# ============================================================
# GIT
# ============================================================

def git_commit_and_push(
    file_name: str,
    commit_message: str
):

    try:

        repo = git.Repo(
            WORKSPACE_ROOT
        )

    except git.InvalidGitRepositoryError:

        return (
            "GIT FAILED: Workspace is not "
            "a Git repository."
        )

    try:

        target = safe_workspace_path(
            file_name
        )

        relative_file = str(
            target.relative_to(
                WORKSPACE_ROOT
            )
        )

        if not target.exists():

            return (
                "GIT FAILED: File does not exist: "
                f"{relative_file}"
            )

        # Stage ONLY the requested file.
        repo.index.add([
            relative_file
        ])

        staged_diff = repo.index.diff(
            "HEAD"
        )

        untracked = [
            item
            for item in repo.untracked_files
            if item == relative_file
        ]

        if not staged_diff and not untracked:

            return (
                "GIT SKIPPED: No changes detected "
                f"for {relative_file}."
            )

        commit = repo.index.commit(
            commit_message
        )

        commit_result = (
            "GIT COMMIT SUCCESSFUL\n"
            f"File: {relative_file}\n"
            f"Commit: {commit.hexsha[:12]}"
        )

        if not repo.remotes:

            return (
                f"{commit_result}\n"
                "GIT PUSH FAILED: "
                "No Git remote is configured."
            )

        try:

            origin = repo.remote(
                "origin"
            )

        except ValueError:

            return (
                f"{commit_result}\n"
                "GIT PUSH FAILED: "
                "No 'origin' remote exists."
            )

        try:

            branch = repo.active_branch.name

        except TypeError:

            return (
                f"{commit_result}\n"
                "GIT PUSH FAILED: "
                "Repository is in detached HEAD state."
            )

        try:

            push_results = origin.push(
                branch
            )

            errors = []

            for push_info in push_results:

                if push_info.flags & (
                    git.remote.PushInfo.ERROR
                    | git.remote.PushInfo.REJECTED
                    | git.remote.PushInfo.REMOTE_REJECTED
                ):

                    errors.append(
                        push_info.summary
                    )

            if errors:

                return (
                    f"{commit_result}\n"
                    "GIT PUSH FAILED:\n"
                    + "\n".join(errors)
                )

            return (
                f"{commit_result}\n"
                f"GIT PUSH SUCCESSFUL\n"
                f"Branch: {branch}\n"
                f"Remote: origin"
            )

        except Exception as push_error:

            return (
                f"{commit_result}\n"
                "GIT PUSH FAILED:\n"
                f"{push_error}"
            )

    except Exception as error:

        return (
            f"GIT OPERATION FAILED: "
            f"{error}"
        )


# ============================================================
# SANITIZATION
# ============================================================

SECRET_PATTERN = re.compile(
    r"(?:"
    r"[a-zA-Z0-9_-]{24,}\.[a-zA-Z0-9_-]{6,}\."
    r"[a-zA-Z0-9_-]{27,}"
    r"|(?:sk|key|ghp|passwd|pwd|secret|token|aws)"
    r"[-_a-zA-Z0-9]{12,64}"
    r"|[a-zA-Z0-9+/=]{32,128}"
    r")"
)


def clean_input_pipeline(
    raw_user_input
):

    if not raw_user_input:
        return ""

    if not raw_user_input.strip():
        return ""

    # Do NOT aggressively redact normal numbers.
    #
    # Coding requests frequently contain:
    #
    # 1024
    # 5000
    # port 8501
    # Python versions
    # dimensions
    # API parameters
    #
    # Redacting them makes coding instructions unreliable.

    found_secrets = SECRET_PATTERN.findall(
        raw_user_input
    )

    for secret in set(found_secrets):

        raw_user_input = raw_user_input.replace(
            secret,
            "[REDACTED_SECRET]"
        )

    scrubber = scrubadub.Scrubber()

    try:

        cleaned = scrubber.clean(
            raw_user_input
        )

    except Exception:

        cleaned = raw_user_input

    return StringSchema.validate_python(
        cleaned
    )


# ============================================================
# TOOLS
# ============================================================

AGENT_TOOLS = [

    {
        "type": "function",
        "function": {

            "name": "create_file",

            "description": (
                "Create or replace a workspace file. "
                "The code argument must contain the COMPLETE "
                "source code to write. Use this whenever "
                "the user asks to create a file and put code "
                "inside it."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "file_name": {
                        "type": "string"
                    },

                    "code": {
                        "type": "string"
                    }
                },

                "required": [
                    "file_name",
                    "code"
                ]
            }
        }
    },

    {
        "type": "function",
        "function": {

            "name": "edit_file",

            "description": (
                "Replace the contents of an existing workspace "
                "file with complete corrected source code."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "file_name": {
                        "type": "string"
                    },

                    "code": {
                        "type": "string"
                    }
                },

                "required": [
                    "file_name",
                    "code"
                ]
            }
        }
    },

    {
        "type": "function",
        "function": {

            "name": "read_file",

            "description": (
                "Read an existing workspace file before "
                "editing or debugging it."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "file_name": {
                        "type": "string"
                    }
                },

                "required": [
                    "file_name"
                ]
            }
        }
    },

    {
        "type": "function",
        "function": {

            "name": "delete_file",

            "description": (
                "Delete a workspace file when the user "
                "explicitly requests deletion."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "file_name": {
                        "type": "string"
                    }
                },

                "required": [
                    "file_name"
                ]
            }
        }
    },

    {
        "type": "function",
        "function": {

            "name": "install_library",

            "description": (
                "Install a Python package when the user "
                "explicitly requests it or when a required "
                "dependency must be installed for the requested "
                "application."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "library_name": {
                        "type": "string"
                    }
                },

                "required": [
                    "library_name"
                ]
            }
        }
    },

    {
        "type": "function",
        "function": {

            "name": "execute_command",

            "description": (
                "Run a normal workspace shell command for "
                "diagnostics, validation, or development."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "command": {
                        "type": "string"
                    }
                },

                "required": [
                    "command"
                ]
            }
        }
    },

    {
        "type": "function",
        "function": {

            "name": "validate_python",

            "description": (
                "Validate a Python file using Python's "
                "py_compile module."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "file_name": {
                        "type": "string"
                    }
                },

                "required": [
                    "file_name"
                ]
            }
        }
    },

    {
        "type": "function",
        "function": {

            "name": "git_commit_and_push",

            "description": (
                "Stage the specified file, commit it, and "
                "push the active branch to the origin remote. "
                "Only use this when the user requests Git "
                "commit/push or when completing an explicit "
                "create-and-push workflow."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "file_name": {
                        "type": "string"
                    },

                    "commit_message": {
                        "type": "string"
                    }
                },

                "required": [
                    "file_name",
                    "commit_message"
                ]
            }
        }
    }
]


# ============================================================
# TOOL EXECUTION
# ============================================================

def execute_tool(tool_call):
    """
    Safely execute one Groq tool call.

    This function NEVER allows a tool exception to crash the
    entire agent loop. Every failure is converted into a string
    that can be returned to the model as a tool result.
    """

    # --------------------------------------------------------
    # 1. Basic tool-call validation
    # --------------------------------------------------------

    if tool_call is None:
        return "TOOL ERROR: Received an empty tool call."

    try:
        function = tool_call.function
    except AttributeError:
        return "TOOL ERROR: Tool call has no function object."

    if function is None:
        return "TOOL ERROR: Tool call function is empty."

    # --------------------------------------------------------
    # 2. Get function name
    # --------------------------------------------------------

    function_name = getattr(
        function,
        "name",
        None
    )

    if not function_name:
        return "TOOL ERROR: Tool call has no function name."

    # --------------------------------------------------------
    # 3. Parse arguments safely
    # --------------------------------------------------------

    raw_arguments = getattr(
        function,
        "arguments",
        None
    )

    if raw_arguments is None:
        raw_arguments = "{}"

    if not isinstance(raw_arguments, str):
        raw_arguments = str(raw_arguments)

    try:
        args = json.loads(raw_arguments)

    except json.JSONDecodeError as error:

        return (
            "TOOL ERROR: Invalid JSON arguments for "
            f"{function_name}.\n"
            f"Parser error: {error}\n"
            f"Raw arguments: {raw_arguments}"
        )

    # --------------------------------------------------------
    # 4. Arguments MUST be a JSON object
    # --------------------------------------------------------

    if not isinstance(args, dict):

        return (
            "TOOL ERROR: Tool arguments must be a JSON "
            f"object for {function_name}."
        )

    # --------------------------------------------------------
    # 5. Explicit tool dispatcher
    #
    # Do NOT dynamically execute arbitrary Python names.
    # --------------------------------------------------------

    available_tools = {
        "create_file": create_or_replace_file,
        "edit_file": edit_file,
        "read_file": read_file,
        "delete_file": delete_file,
        "install_library": install_library,
        "execute_command": ask_for_command_and_execute_command,
        "validate_python": validate_python_file,
        "git_commit_and_push": git_commit_and_push,
    }

    function_to_call = available_tools.get(
        function_name
    )

    if function_to_call is None:

        return (
            "TOOL ERROR: Unknown tool requested: "
            f"{function_name}\n"
            "Available tools: "
            + ", ".join(available_tools.keys())
        )

    # --------------------------------------------------------
    # 6. Validate expected arguments per tool
    # --------------------------------------------------------

    required_arguments = {

        "create_file": [
            "file_name",
            "code"
        ],

        "edit_file": [
            "file_name",
            "code"
        ],

        "read_file": [
            "file_name"
        ],

        "delete_file": [
            "file_name"
        ],

        "install_library": [
            "library_name"
        ],

        "execute_command": [
            "command"
        ],

        "validate_python": [
            "file_name"
        ],

        "git_commit_and_push": [
            "file_name",
            "commit_message"
        ],
    }

    required = required_arguments.get(
        function_name,
        []
    )

    missing = [
        argument
        for argument in required
        if argument not in args
    ]

    if missing:

        return (
            "TOOL ERROR: Missing required argument(s) "
            f"for {function_name}: "
            + ", ".join(missing)
        )

    # --------------------------------------------------------
    # 7. Explicit argument mapping
    #
    # This is safer than:
    #
    # function_to_call(**args)
    #
    # because it prevents unexpected arguments from
    # reaching your Python functions.
    # --------------------------------------------------------

    try:

        if function_name == "create_file":

            return create_or_replace_file(
                file_name=args["file_name"],
                code=args["code"]
            )

        if function_name == "edit_file":

            return edit_file(
                file_name=args["file_name"],
                code=args["code"]
            )

        if function_name == "read_file":

            return read_file(
                file_name=args["file_name"]
            )

        if function_name == "delete_file":

            return delete_file(
                file_name=args["file_name"]
            )

        if function_name == "install_library":

            return install_library(
                library_name=args["library_name"]
            )

        if function_name == "execute_command":

            return ask_for_command_and_execute_command(
                command=args["command"]
            )

        if function_name == "validate_python":

            return validate_python_file(
                file_name=args["file_name"]
            )

        if function_name == "git_commit_and_push":

            return git_commit_and_push(
                file_name=args["file_name"],
                commit_message=args["commit_message"]
            )

        return (
            "TOOL ERROR: Dispatcher reached an unexpected "
            f"tool: {function_name}"
        )

    except Exception as error:

        # ----------------------------------------------------
        # NEVER let a tool crash the agent.
        # Return the error to the model instead.
        # ----------------------------------------------------

        return (
            "TOOL EXECUTION ERROR\n"
            f"Tool: {function_name}\n"
            f"Error type: {type(error).__name__}\n"
            f"Error: {error}"
        )


# ============================================================
# AGENT
# ============================================================

def final_ai_agent(
    user_input,
    model="openai/gpt-oss-120b"
):
    """
    Autonomous Groq workspace coding agent.

    Workflow:

        User
          ↓
        Groq
          ↓
        Tool call(s)
          ↓
        Local Python execution
          ↓
        Tool result(s)
          ↓
        Groq
          ↓
        More tools OR final answer

    The conversation is preserved throughout the entire
    tool-calling process.
    """

    # ========================================================
    # 1. SANITIZE USER INPUT
    # ========================================================

    sanitized_input = clean_input_pipeline(
        user_input
    )

    if not sanitized_input:

        return (
            "AI: Please provide a request."
        )

    # ========================================================
    # 2. SYSTEM PROMPT
    # ========================================================

    system_prompt = f"""
You are an autonomous private workspace coding agent.

WORKSPACE:
{WORKSPACE_ROOT}

AVAILABLE TOOLS:
create_file
edit_file
read_file
delete_file
install_library
execute_command
validate_python
git_commit_and_push

============================================================
CORE RULES
============================================================

1. You are an ACTION AGENT.

When the user asks you to create, edit, read, delete,
validate, install, execute, commit, or push something,
actually use the appropriate tool.

Do NOT merely describe what you would do.

------------------------------------------------------------

2. FILE CREATION

When the user asks:

"create a file"

"make a file"

"write code in a file"

"create app.py"

"write the code for X into Y.py"

you MUST use create_file.

The "code" argument must contain the COMPLETE source code.

Never send partial code.

------------------------------------------------------------

3. FILE EDITING

Before modifying an existing file:

1. Use read_file when the existing contents matter.
2. Produce the COMPLETE corrected source.
3. Use edit_file.
4. Validate it when appropriate.

Do not describe edits without performing them.

------------------------------------------------------------

4. PYTHON VALIDATION

After creating or editing a Python file:

Use:

validate_python

If validation fails:

1. Read the error.
2. Fix the source using edit_file.
3. Validate again.

Do not claim that Python code is valid unless validation
actually succeeds.

------------------------------------------------------------

5. DEPENDENCIES

Only install packages when:

- the user explicitly requests installation, OR
- the requested application genuinely requires the package.

Use install_library.

------------------------------------------------------------

6. GIT WORKFLOW

If the user requests commit/push:

The required sequence is:

CREATE/EDIT
    ↓
VALIDATE
    ↓
COMMIT
    ↓
PUSH

Never commit before the requested file is successfully
created/edited and validated.

Use git_commit_and_push only when the user actually asks
for Git commit/push.

------------------------------------------------------------

7. TOOL ERRORS

If a tool reports an error:

Do NOT pretend it succeeded.

Analyze the returned error.

If the problem is fixable, use another tool to correct it.

If it cannot be fixed, clearly report the failure.

------------------------------------------------------------

8. TOOL CALLING

Use the smallest number of tool calls necessary.

Multiple independent tool calls may be requested together.

Do not repeatedly call the same successful tool without reason.

------------------------------------------------------------

9. FINAL RESPONSE

Only produce a final response after the requested operation
is complete, blocked, or has reached the operation limit.

The final response must accurately describe:

- what was done
- files changed
- validation results
- package installations
- Git results
- failures, if any

NEVER claim that an operation succeeded unless a tool result
confirms that it succeeded.

------------------------------------------------------------

10. CASUAL CONVERSATION

If the user is only chatting or asking a normal question
that requires no workspace operation, answer normally without
using tools.

============================================================
WORKSPACE SAFETY
============================================================

The application itself enforces workspace path restrictions.

Do not attempt to bypass them.

Do not invent tool results.

Do not claim access to files that you have not read.

============================================================
CURRENT WORKSPACE
============================================================

{WORKSPACE_ROOT}
"""

    # ========================================================
    # 3. INITIAL MESSAGE STATE
    # ========================================================

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": sanitized_input
        }
    ]

    # ========================================================
    # 4. EXECUTION REPORT
    # ========================================================

    execution_results = []

    # Maximum number of model → tool cycles.
    #
    # Example:
    #
    # create
    # validate
    # edit
    # validate
    # commit
    #
    # = 5 rounds
    #
    MAX_TOOL_ROUNDS = 12

    # ========================================================
    # 5. AGENT LOOP
    # ========================================================

    try:

        for round_number in range(
            1,
            MAX_TOOL_ROUNDS + 1
        ):

            # ------------------------------------------------
            # Ask Groq what to do next.
            # ------------------------------------------------

            response = client.chat.completions.create(

                model=model,

                messages=messages,

                tools=AGENT_TOOLS,

                tool_choice="auto",

                # Explicitly disable parallel calls.
                #
                # This makes the workflow deterministic and
                # especially useful for file-edit/validate/Git
                # sequences where ordering matters.
                parallel_tool_calls=False,

                temperature=0,

                max_completion_tokens=8000
            )

            # ------------------------------------------------
            # Validate API response structure.
            # ------------------------------------------------

            if (
                not response.choices
            ):

                return (
                    "AI:\n\n"
                    "Groq returned no choices."
                )

            ai_message = (
                response.choices[0].message
            )

            tool_calls = (
                ai_message.tool_calls
                or []
            )

            # =================================================
            # NO TOOL CALL = FINAL ANSWER
            # =================================================

            if not tool_calls:

                final_text = (
                    ai_message.content
                    or "The operation has completed."
                )

                report = (
                    "\n\n".join(
                        execution_results
                    )
                    if execution_results
                    else "No tools were executed."
                )

                return (
                    "AI:\n\n"
                    f"{final_text}\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "WORKSPACE EXECUTION REPORT\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{report}"
                )

            # =================================================
            # PRESERVE THE ASSISTANT TOOL-CALL MESSAGE
            # =================================================

            #
            # IMPORTANT:
            #
            # NEVER delete this message.
            #
            # The tool result references its tool_call_id.
            # Groq needs the original assistant tool-call
            # message followed by the corresponding tool result.
            #

            messages.append(
                ai_message
            )

            # =================================================
            # EXECUTE TOOL CALLS
            # =================================================

            for tool_call in tool_calls:

                function_name = getattr(
                    getattr(
                        tool_call,
                        "function",
                        None
                    ),
                    "name",
                    "unknown"
                )

                tool_call_id = getattr(
                    tool_call,
                    "id",
                    None
                )

                # ---------------------------------------------
                # Missing tool-call ID
                # ---------------------------------------------

                if not tool_call_id:

                    result = (
                        "TOOL ERROR: Groq returned a tool call "
                        "without a tool_call_id."
                    )

                else:

                    result = execute_tool(
                        tool_call
                    )

                # ---------------------------------------------
                # Record local execution report
                # ---------------------------------------------

                execution_results.append(
                    f"ROUND: {round_number}\n"
                    f"TOOL: {function_name}\n"
                    f"RESULT:\n{result}"
                )

                # ---------------------------------------------
                # Return tool result to Groq
                # ---------------------------------------------

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "name": function_name,
                        "content": str(result)
                    }
                )

        # ====================================================
        # MAXIMUM ROUND LIMIT
        # ====================================================

        return (
            "AI:\n\n"
            "The agent reached its maximum operation "
            f"limit of {MAX_TOOL_ROUNDS} rounds.\n\n"
            "The agent stopped safely rather than "
            "continuing indefinitely.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "WORKSPACE EXECUTION REPORT\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            +
            (
                "\n\n".join(
                    execution_results
                )
                if execution_results
                else "No tools were executed."
            )
        )

    # ========================================================
    # GROQ/API ERROR
    # ========================================================

    except Exception as error:

        return (
            "AI:\n\n"
            "The agent encountered an error while "
            "processing the request.\n\n"
            f"Error type: {type(error).__name__}\n"
            f"Error: {error}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "WORKSPACE EXECUTION REPORT\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            +
            (
                "\n\n".join(
                    execution_results
                )
                if execution_results
                else "No tools were executed."
            )
        )

def main(page: ft.Page):
    import flet as ft
    page.theme_mode = ft.ThemeMode.DARK
    page.title = "YF AI Private Code Writer"
    page.bgcolor = "black"

    # Title label header reference
    title = ft.Text(
        "YF AI SECURE CODE WRITER",
        size=15,
        color="amber",
    )

    # Core layout viewport scroll engine
    chat_history = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
    )

    # Initialize chat history stream arrays securely
    history = []
    try:
        history = load_chat_history()
    except NameError:
        # Fallback local container setup if load utility is absent
        pass

    for message in history:
        chat_history.controls.append(
            ft.Text(message.get("text", ""), color="white")
        )

    # Declare references early to ensure python namespace tracking handles hooks safely
    user_input = None

    # =========================================================================
    # 2. INTERACTIVE USER INPUT ANIMATION ENGINE
    # =========================================================================
    def handle_input_change(e):
        if user_input:
            has_text = bool(user_input.value.strip())
            # Changes color dynamically to whatever theme is active in settings
            send_btn.bgcolor = color_dropdown.value if has_text else "grey800"
            send_btn.opacity = 1.0 if has_text else 0.3
            send_btn.disabled = not has_text
            send_btn.update()

    # =========================================================================
    # 3. INTERACTIVE CHAT ENGINE WITH DUAL OVERRIDE VALUES
    # =========================================================================
    def send_click(e):
        text_payload = user_input.value.strip()
        if text_payload:
            user_display = f"You: {text_payload}"
            chat_history.controls.append(ft.Text(user_display, color="white"))
            history.append({"text": user_display})
            try: save_chat_history(history)
            except NameError: pass

            # Extract selected layout parameters to parse downstream strings
            chosen_model_string = model_dropdown.value

            user_input.value = ""
            handle_input_change(None) # Instantly dims button back to grey on text wipe
            page.update()

            try:
                text_payload = clean_input_pipeline(text_payload)
                # CRUCIAL ROUTER: Passes exactly the two arguments you specified
                text = final_ai_agent(text_payload, model=chosen_model_string)
            except NameError:
                # Local mock fallback execution handling for independent standalone executions
                text = f"[Local Agent Mock Mode] Running execution sequence via: {chosen_model_string}\nProcessed Code Payload successfully."

            ai_display_string = f"YF AI:\n{text}"
            chat_history.controls.append(ft.Text(ai_display_string, color="white"))
            history.append({"text": ai_display_string})
            try: save_chat_history(history)
            except NameError: pass
            page.update()

    # =========================================================================
    # 4. CAPSULE LAYOUT COMPONENT CONSTRUCTORS
    # =========================================================================
    send_btn = ft.ElevatedButton(
        content=ft.Icon(
            ft.Icons.ARROW_UPWARD,
            color="yellow",
            size=18
        ),
        bgcolor="blue",
        opacity=1.0,
        disabled=True,
        on_click=send_click,
    )

    user_input = ft.TextField(
        hint_text="Ask the agent to write code (e.g. 'Create a script inside src/utils.py')...",
        expand=True,
        bgcolor="black",
        border_color="white",
        focused_border_color="white",
        text_style=ft.TextStyle(color="white"),
        on_change=handle_input_change,
    )

    input_row = ft.Row(
        controls=[
            user_input,
            send_btn,
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    app_content = ft.Column(
        controls=[
            ft.Row(controls=[title], alignment=ft.MainAxisAlignment.CENTER),
            chat_history,
            input_row,
        ],
        expand=True,
    )

    logo_image = ft.Image(
        src="/company.png",
        width=40,
            height=40,
            fit=ft.BoxFit.CONTAIN,
            top=5,
            left=5,
        )

        # =========================================================================
        # 5. MODULAR CONTROL DASHBOARD & SETTINGS OVERLAYS
        # =========================================================================

    def change_accent_color(e):
        # Fetch the lowercase color value (e.g., "amber", "blue")
        selected_color = color_dropdown.value.lower()

        # Apply the accent color seed to the app theme
        page.theme = ft.Theme(color_scheme_seed=selected_color)
        page.update()

    # 1. Create the dropdown with ZERO events inside it to prevent errors
    color_dropdown = ft.Dropdown(
        label="App Accent Theme Color",
        value="amber",
        options=[
            ft.dropdown.Option("amber", "Amber Gold"),
            ft.dropdown.Option("blue", "Deep Sea Blue"),
            ft.dropdown.Option("green", "Hacker Green"),
            ft.dropdown.Option("purple", "Cyber Neon Purple"),
        ],
    )

    # 2. Bind the event directly on its own line (Bypasses __init__ keyword validation)
    color_dropdown.on_change = change_accent_color

    # Feature 2: Core Consolidated Multi-Model Dropdown Option Matrix
    model_dropdown = ft.Dropdown(
        label="Target Language Model",
        value="llama-3.3-70b-versatile", # Default safe state engine assignment
    options=[
        ft.dropdown.Option("openai/gpt-4o", "GPT-4o (OpenAI Omni)"),
        ft.dropdown.Option("openai/gpt-4o-mini", "GPT-4o-Mini (OpenAI Mini)"),
        ft.dropdown.Option("qwen/qwen-coder-32b", "Qwen 2.5 Coder (Alibaba Code)"),
        ft.dropdown.Option("deepseek/deepseek-coder", "DeepSeek-Coder-V2 (Math & Code)"),
        ft.dropdown.Option("openai/gpt-oss-120b", "GPT-OSS-120B (OpenAI OSS)"),
        ft.dropdown.Option("openai/gpt-oss-20b", "GPT-OSS-20B (OpenAI OSS)")])

    # Feature 3: Clear Chat Cache Storage Routine
    def wipe_chat_cache(e):
        delete_file("chat_history.json")
    clear_history_btn = ft.ElevatedButton(
        "Wipe Chat Cache Context",
        icon=ft.Icons.DELETE_FOREVER,
        color="white",
        bgcolor="red800",
        on_click=wipe_chat_cache
    )

    # Setup the Material Alert Dialog layout container
    settings_dialog = ft.AlertDialog(
        title=ft.Text("YF AI Control Dashboard", size=20, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            controls=[
                ft.Text("Manage dashboard themes, assign core model target string paths, and purge session logs safely.", size=12, color="grey400"),
                ft.Divider(height=10, color="transparent"),
                color_dropdown,
                ft.Divider(height=5, color="grey800"),
                ft.Text("Model Configuration Layer", size=14, weight=ft.FontWeight.W_500),
                model_dropdown,
                ft.Divider(height=5, color="grey800"),
                ft.Text("System Memory Actions", size=14, weight=ft.FontWeight.W_500),
                clear_history_btn
            ],
            tight=True,
            spacing=15
        ),
        actions=[
            ft.TextButton("Close Settings", on_click=lambda e: setattr(settings_dialog, "open", False) or page.update())
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # Store settings dialog inside page overlays configuration matrix safely
    page.overlay.append(settings_dialog)

    # Open Settings Modal Event Action Routine
    def open_settings(e):
        settings_dialog.open = True
        page.update()

    # Float a gears settings tracking icon safely over the top right canvas corner grid
    settings_btn = ft.ElevatedButton(
        content=ft.Icon(ft.Icons.SETTINGS, color="white", size=22),
        top=10,
        right=10,
        on_click=open_settings,
    )
    import io

    import base64

    import os

    from pathlib import Path
    import flet as ft
    import flet_video as ftv
    import torch
    from diffusers import StableDiffusionXLPipeline

    # 1. Global storage and pipeline memory allocation variables
    image_history = []
    current_image_index = -1
    local_image_pipe = None  # Holds model in memory to prevent reloading

    # Text Input Field with fixed dimensions so Flet cannot crush it
    image_prompt_input = ft.TextField(
        hint_text="Describe the image you want to create...",
        width=500,
        height=50,
        bgcolor="black",
        border_color="white",
        focused_border_color="white",
        text_style=ft.TextStyle(color="white")
    )

    # Main visual display widget with a stable local file placeholder setup
    ai_image_display = ft.Image(
        src="https://placehold.co",
        width=400,
        height=400,
        fit="contain",
        visible=True
    )

    # Local layout loader wheel
    loading_indicator = ft.ProgressRing(visible=False, color="blueaccent")

    # Fixed Thumbnail grid manager component
    history_grid = ft.GridView(
        height=100,
        runs_count=5,
        max_extent=120,
        child_aspect_ratio=1.0,
        spacing=10,
        run_spacing=10,
    )

    # 2. LOCAL PIPELINE IMAGE GENERATION FUNCTION
    def run_image_generation(e):
        global image_history, current_image_index

        local_image_pipe = None

        from diffusers import StableDiffusionXLPipeline

        loading_indicator.visible = True

        page.update()

        try:
            prompt_text = image_prompt_input.value
            if not prompt_text:
                image_prompt_input.hint_text = "⚠️ Prompt cannot be empty!"
                page.update()
                return

            # Check your local processing environment (CUDA GPU vs local CPU cycles)
            device = "cuda" if torch.cuda.is_available() else "cpu"

            # Lazy-load the pipeline only once to prevent RAM lockups
            if local_image_pipe is None:
                print(f"⏳ Downloading/Loading local SDXL pipeline into {device.upper()} compute memory...")
                model_id = "stabilityai/stable-diffusion-xl-base-1.0"

                local_image_pipe = StableDiffusionXLPipeline.from_pretrained(
                    model_id,
                    torch_dtype=torch.float32 if device == "cpu" else torch.float16,
                    variant="fp16" if device == "cuda" else None,
                    use_safetensors=True
                )
                local_image_pipe.to(device)

            print(f"🎨 Computing local weights matrix vectors for prompt: '{prompt_text}'")
            # num_inference_steps=20 ensures rapid computing loops on laptops
            result = local_image_pipe(prompt=prompt_text, num_inference_steps=20)
            image = result.images[0]

            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()

            generated_b64_string = base64.b64encode(img_bytes).decode('utf-8')

            # Append transaction node metrics to history tracker
            new_image_data = {
                "b64_string": generated_b64_string,
                "prompt": prompt_text
            }
            image_history.append(new_image_data)
            current_image_index = len(image_history) - 1

            # Render straight onto your viewport layout screen
            ai_image_display.src = f"data:image/png;base64,{generated_b64_string}"
            ai_image_display.visible = True

            # Clean update grid call
            update_history_ui()

        except Exception as error:
            image_prompt_input.hint_text = f"❌ Local Pipe Error: {repr(error)}"
            print(f"Image run error context trace: {repr(error)}")

        finally:
            loading_indicator.visible = False
            page.update()

    def update_history_ui():
        """Clears and rebuilds the history thumbnail grid (CONTAINER FREE)."""
        history_grid.controls.clear()

        for index, img_data in enumerate(reversed(image_history)):
            true_index = len(image_history) - 1 - index

            # Maintained pure ft.Image mapping constraint rules
            thumbnail = ft.GestureDetector(
                content=ft.Image(
                    src=f"data:image/png;base64,{img_data['b64_string']}",
                    fit="cover",

                    border_radius=8,
                    width=100,
                    height=100
                ),
                on_tap=lambda x, idx=true_index: load_historic_image(idx)
            )
            history_grid.controls.append(thumbnail)

        history_grid.update()

    def load_historic_image(index):

        """Loads a previously generated image back into the main view."""

        global current_image_index

        current_image_index = index

        img_data = image_history[index]

        ai_image_display.src = f"data:image/png;base64,{img_data['b64_string']}"

        image_prompt_input.value = img_data['prompt']

        update_history_ui()

        page.update()

    def download_image(e):
        global image_history, current_image_index

        if current_image_index == -1 or not image_history:

            image_prompt_input.hint_text = "❌ Error: No image selected!"

            page.update()

            return

        try:
            active_image = image_history[current_image_index]

            downloads_path = Path.home() / "Downloads"

            safe_prompt = "".join(x for x in active_image['prompt'][:15] if x.isalnum() or x in "._- ")

            output_filepath = downloads_path / f"AI_{safe_prompt or 'image'}.png"

            image_bytes = base64.b64decode(active_image['b64_string'])

            with open(output_filepath, "wb") as file:

                file.write(image_bytes)

            image_prompt_input.hint_text = "✅ Saved active image to Downloads!"

            page.update()

        except Exception as error:

            image_prompt_input.hint_text = f"❌ Failed to save: {error}"

            page.update()

    import os

    import shutil

    import flet as ft

    import flet_video as ftv

    import torch

    from diffusers import DiffusionPipeline

    # Global tracking variables mapping your local system file paths
    video_link = ""

    # FIXED: Replaced expand=True with width=500 to fix the disappearing layout bug
    prompt = ft.TextField(
        hint_text="Describe the video you want to create (e.g. 'A Cat walking...')...",
        width=500,
        bgcolor="black",
        border_color="white",
        focused_border_color="white",
        text_style=ft.TextStyle(color="white")
    )
    local_video_pipe = None  # Holds the video model in memory to prevent slow reloads

    def generate_ltx_video(e):
        global video_link, local_video_pipe

        # Guard check: Ensure prompt isn't blank
        if not prompt.value:

            prompt.error_text = "⚠️ Prompt cannot be empty!"

            page.update()

            return

        # Freeze interactive controls and toggle the loading indicator ring on
        submit_vid_btn.disabled = True

        loading_indicator.visible = True

        prompt.error_text = ""

        page.update()

        try:
            # Check local computer environment (NVIDIA GPU vs Local CPU)
            device = "cuda" if torch.cuda.is_available() else "cpu"

            # Lazy-load the video pipeline only once into memory to save RAM
            if local_video_pipe is None:

                print(f"⏳ Loading free local video generation pipeline onto {device.upper()}...")
                # Using a tiny, fast model optimized to complete rapidly on laptop components
                model_id = "jbilcke-hf/videos"

                local_video_pipe = DiffusionPipeline.from_pretrained(
                    model_id,
                    torch_dtype=torch.float32 if device == "cpu" else torch.float16
                )
                local_video_pipe.to(device)

            print(f"🎬 Local pipeline is computing video frames for prompt: '{prompt.value}'")
            # num_inference_steps=15 keeps computing times fast on non-gaming laptops
            video_frames = local_video_pipe(prompt.value, num_inference_steps=15).frames

            if not os.path.exists("assets"):
                os.makedirs("assets")

            local_path = "assets/temp_ltx_output.mp4"

            # Use your pipeline tool logic export wrapper to write the file directly to your disk
            # (The local pipeline package automatically handles frame stitching seamlessly)
            video_frames.save(local_path)

            # Bind the file path variables back up to your global tracking variable
            video_link = local_path

            video_player.playlist = [ftv.VideoMedia(local_path)]

            download_vid_btn.disabled = False

            prompt.error_text = ""

            print(f"✅ Success! Local video frames written safely to: {local_path}")

        except Exception as ex:

            prompt.error_text = f"❌ Local Video Pipe Error: {repr(ex)}"

            print(f"Generation error hit: {repr(ex)}")

        finally:
            # Re-enable app buttons and hide loading overlays smoothly
            submit_vid_btn.disabled = False

            loading_indicator.visible = False

            page.update()

    def download_vid(e):
        global video_link

        if not video_link or not os.path.exists(video_link):

            print("No valid generated video file discovered to download yet.")

            return

        try:
            # Map out path destination straight to your laptop system Downloads folder
            downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")

            save_path = os.path.join(downloads_folder, "yf_ltx_video.mp4")

            # Since the file sits on your storage device already, copy it with zero internet drag
            shutil.copy(video_link, save_path)

            # Show a success alert banner down across the bottom viewport
            page.snack_bar = ft.SnackBar(ft.Text(f"🚀 Video successfully saved to: {save_path}"), open=True)

            page.update()

        except Exception as ex:

            print(f"An error occurred during file duplicate download layout: {ex}")

    # ELEVATED BUTTONS FOR ACTIONS
    submit_vid_btn = ft.ElevatedButton(
        content=ft.Icon(ft.Icons.ARROW_UPWARD, color="yellow", size=22),
        on_click=generate_ltx_video
    )

    download_vid_btn = ft.ElevatedButton(
        content=ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, color="yellow", size=22),
        on_click=download_vid
    )

    video_player = ftv.Video(
        expand=True,
        playlist=[ftv.VideoMedia(video_link)] if video_link else [],
        playlist_mode=ftv.PlaylistMode.LOOP,
        fill_color=ft.Colors.BLACK,
        aspect_ratio=16 / 9,
        autoplay=True,
        controls=True,
    )

    # ELEVATED BUTTONS FOR MEDIA
    submit_gen_btn = ft.ElevatedButton(
        content=ft.Icon(ft.Icons.ARROW_UPWARD, color="yellow", size=22),
        on_click=run_image_generation
    )

    download_btn = ft.ElevatedButton(
        content=ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, color="yellow", size=22),
        on_click=download_image
    )

    # 1. IMAGE GENERATION DIALOG (No Containers inside Controls Stack)
    gen_dialog = ft.AlertDialog(
        title=ft.Text("YF AI Image Creation", size=20, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            controls=[
                ft.Text("Create images using Hugging Face models.", size=12, color="grey400"),
                ft.Divider(height=10, color="transparent"),
                image_prompt_input,
                submit_gen_btn,
                loading_indicator,
                ft.Divider(height=5, color="grey800"),
                ft.Text("Output Preview Area", size=14, weight=ft.FontWeight.W_500),
                ai_image_display,
                ft.Divider(height=5, color="grey800"),
                ft.Text("Download file", size=14, weight=ft.FontWeight.W_500),
                download_btn,
                ft.Divider(height=5, color="grey800"),
                ft.Text("Image History", size=14, weight=ft.FontWeight.W_500),
                history_grid
            ],
            tight=True,
            spacing=15
        ),
        actions=[
            ft.TextButton("Close Canvas", on_click=lambda e: setattr(gen_dialog, "open", False) or page.update())
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # 2. VIDEO GENERATION DIALOG (No Containers inside Controls Stack)
    gen_video_dialog = ft.AlertDialog(
        title=ft.Text("YF AI Video Creation", size=20, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            controls=[
                ft.Text("Create videos using Hugging Face models.", size=12, color="grey400"),
                ft.Divider(height=10, color="transparent"),
                prompt,
                submit_vid_btn,
                loading_indicator,
                ft.Divider(height=5, color="grey800"),
                ft.Text("Output Preview Area", size=14, weight=ft.FontWeight.W_500),
                video_player if video_link else ft.Text("No video generated yet. Type a prompt above and press upload!",
                                                        color="grey500"),
                ft.Divider(height=5, color="grey800"),
                ft.Text("Download file", size=14, weight=ft.FontWeight.W_500),
                download_vid_btn,
            ],
            tight=True,
            spacing=15
        ),
        actions=[
            ft.TextButton("Close Canvas", on_click=lambda e: setattr(gen_video_dialog, "open", False) or page.update())
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # Store BOTH layout dialog configurations inside page overlays tree safely
    page.overlay.append(gen_dialog)

    page.overlay.append(gen_video_dialog)

    def open_image_gen_page(e):
        gen_dialog.open = True
        page.update()

    def open_vid_gen_page(e):
        gen_video_dialog.open = True
        page.update()

    # NAVIGATION TRIGGERS (Positioned via Absolute Stack rules, Container Free)
    image_generation = ft.ElevatedButton(
        content=ft.Icon(ft.Icons.IMAGE_SEARCH, color=ft.Colors.BLUE_ACCENT_400, size=14),
        top=10, right=90,
        on_click=open_image_gen_page
    )

    video_generation = ft.ElevatedButton(
        content=ft.Icon(ft.Icons.VIDEO_CALL, color=ft.Colors.PINK_ACCENT_400, size=14),
        top=10, right=160,
        on_click=open_vid_gen_page
    )
    # =========================================================================
    main_layout_stack = ft.Stack(
        controls=[
            app_content,
            logo_image,
            settings_btn,
            image_generation,
            video_generation
        ],
        expand=True,
    )

    page.add(main_layout_stack)


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550)