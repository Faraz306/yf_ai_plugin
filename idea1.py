import os
import json
import sys
import subprocess
from pathlib import Path
import git
from groq import Groq
from pydantic import TypeAdapter
import requests
import re
# ============================================================
# CONFIGURATION
# ============================================================
CHAT_FILE = "chat_history_"
def get_current_repo_slug_automatically():
    """
    Scans the local PyCharm project working directory, reads your local
    Git origin tracking links, and automatically extracts the 'username/repo' handle.
    """
    try:
        # 1. Run a native terminal check to pull down the tracking URL string
        # This works dynamically on any machine with Git installed
        origin_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            text=True
        ).strip()

        print(f"🔍 Local Git configuration detected remote link: {origin_url}")

        # 2. Extract out the slug handles matching both HTTPS and SSH variants
        # e.g., 'https://github.com' -> 'Faraz306/yf_ai_plugin'
        # e.g., 'git@github.com:Faraz306/yf_ai_plugin.git'    -> 'Faraz306/yf_ai_plugin'
        match = re.search(r"github\.com[:/]([^/]+/[^.]+)", origin_url)

        if match:
            slug = match.group(1)
            # Remove trailing '.git' modifications if they exist in configuration files
            if slug.endswith(".git"):
                slug = slug[:-4]
            return slug

    except Exception as e:
        print(f"⚠️ Git configuration read loop skipped: {e}")

    # Fallback to a plain tracking parameter string if the project folder lacks a Git history init
    return None


def dispatch_async_cloud_job(task_prompt, current_user_id):
    github_token = os.getenv("GITHUB_TOKEN")
    repo_slug = get_current_repo_slug_automatically()

    if not repo_slug:
        print("❌ Critical Failure: Could not automatically detect a valid GitHub remote origin in this project!")
        return False

    if not github_token:
        print("❌ Critical Failure: GITHUB_TOKEN is not set in the environment.")
        return False

    print(f"🚀 Targeted Orchestration Target Resolved: {repo_slug}")
    dispatch_url = f"https://api.github.com/repos/{repo_slug}/dispatches"

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "Faraz306",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    payload = {
        "event_type": "yf_remote_agent_task",
        "client_payload": {
            "task": task_prompt,
            "user_id": current_user_id
        }
    }

    try:
        res = requests.post(dispatch_url, headers=headers, json=payload, timeout=15)
    except Exception as e:
        print(f"❌ Network/Error sending dispatch: {e}")
        return False

    # Success for repository_dispatch returns 204 No Content
    if res.status_code == 204:
        print("✅ Cloud dispatch accepted (204 No Content).")
        return True

    # Otherwise print server response and return False
    print(f"❌ GitHub API Error Status Code: {res.status_code}")
    print(f"📝 GitHub Server Error Response Body: {res.text}")
    print(f"🔑 Debug - Token loaded: {'Yes (starts with ' + github_token[:8] + '...)' if github_token else 'No (None/Empty)'}")
    print(f"📦 Debug - Payload structure: {json.dumps(payload, indent=2)}")
    return False

client = Groq(api_key="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")

StringSchema = TypeAdapter(str)


# ============================================================
# CHAT HISTORY
# ============================================================

def load_chat_history(user_id):
    if not os.path.exists(f"{CHAT_FILE}{user_id}"):
        return []

    try:
        with open(
            f"{CHAT_FILE}{user_id}",
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return []


def save_chat_history(history, user_id):
    with open(f"{CHAT_FILE}{user_id}", "w", encoding="utf-8") as file:
        file.write(history)
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


def ask_for_command_and_execute_command(command: str):

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
            timeout=30,
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        # 🚀 YF AI TOKEN SHIELD: Slices oversized outputs to protect the 6,000 TPM limit
        if len(stdout) > 500:
            stdout = (
                stdout[:500]
                + "\n... [TRUNCATED BY YF AI TO PROTECT CONTEXT BOUNDARIES]"
            )

        if len(stderr) > 500:
            stderr = (
                stderr[:500]
                + "\n... [TRUNCATED BY YF AI TO PROTECT CONTEXT BOUNDARIES]"
            )

        output_parts = []

        if stdout:
            output_parts.append("STDOUT:\n" + stdout)

        if stderr:
            output_parts.append("STDERR:\n" + stderr)

        if not output_parts:

            output_parts.append("Command completed with no output.")

        output_parts.append(f"Exit code: {result.returncode}")

        return "\n\n".join(output_parts)

    except subprocess.TimeoutExpired:

        return "Command timed out after " "30 seconds."

    except Exception as error:

        return f"Execution error: {error}"

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
import math
import scrubadub


def calculate_entropy(text: str) -> float:
    """Calculates Shannon Entropy to catch truly random keys without regex."""
    if not text:
        return 0.0
    frequencies = {}

    for char in text:

        frequencies[char] = frequencies.get(char, 0) + 1
    entropy = 0.0
    total_len = len(text)
    for count in frequencies.values():
        p = count / total_len
        entropy -= p * math.log2(p)
    return entropy


def clean_input_pipeline(raw_user_input: str) -> str:
    if not raw_user_input or not raw_user_input.strip():
        return ""

    # Safe lists to bypass tracking (Covers your 8501, 1024, version tokens)
    # Since we use entropy/length, normal numbers and short ports are naturally ignored!
    safe_keywords = {"python", "amd64", "version", "port"}

    # 1. Non-regex Secret Scanning via Content Splitting & Entropy Analysis
    # Splits by common characters found in code variables or strings
    words = [w.strip('"\'=:,;()[]{}') for w in raw_user_input.split()]
    found_secrets = set()

    for word in words:
        # High-entropy thresholds (>=4.3) cleanly pick up real API keys,
        # JWT tokens, and hashes while ignoring standard words or standard integers.
        if len(word) >= 20 and word.lower() not in safe_keywords:
            # Confirm it's a mixed string (has letters AND numbers/symbols) to prevent clearing huge flat text blocks
            if any(c.isdigit() or c in "+/=-_" for c in word) and any(c.isalpha() for c in word):
                if calculate_entropy(word) > 4.2:
                    found_secrets.add(word)

    # Redact identified entropy structures
    for secret in found_secrets:
        raw_user_input = raw_user_input.replace(secret, "[REDACTED_SECRET]")

    # 2. PII Cleanup Pipeline (Names, Emails, IP Addresses) via scrubadub
    scrubber = scrubadub.Scrubber()
    try:
        cleaned = scrubber.clean(raw_user_input)
    except Exception:
        cleaned = raw_user_input

    return StringSchema.validate_python(cleaned)


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
    model="llama-3.1-8b-instant",
    user_id="guest"  # 1. ADD USER_ID AS A PARAMETER

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
    import os
    HISTORY = read_history()

    # ========================================================
    # 2. SYSTEM PROMPT
    # ========================================================
    USER_WORKSPACE_ROOT = os.path.join(WORKSPACE_ROOT, f"workspace_{user_id}")

    system_prompt = f"""
You are an autonomous private workspace coding agent.

WORKSPACE:
{USER_WORKSPACE_ROOT}
USER_HISTORY:
{HISTORY}
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

merely describe what you would do.

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

                max_completion_tokens=2000
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
                    if function_name in ["create_file", "edit_file"]:

                        # Extract arguments safely from the tool call
                        import json
                        import ast
                        import os

                        try:
                            args = json.loads(tool_call.function.arguments)
                            # Grab file details from args (fallback to generic if missing)
                            file_code = args.get("code") or args.get("content", "")
                            file_name = args.get("file_name") or args.get("file_path", "app.py")

                            # Only parse if it's meant to be a Python script
                            if file_name.endswith(".py") and file_code:
                                try:
                                    # AST parses code strings instantly without running them
                                    ast.parse(file_code)
                                except SyntaxError as syntax_err:
                                    # Intercept the success message! Force Groq to see the bug.
                                    result = (
                                        f"CRITICAL ERROR: Code saved in '{file_name}' contains a syntax error!\n"
                                        f"Line {syntax_err.lineno}: {syntax_err.msg}\n"
                                        f"Code snippet with issue:\n{syntax_err.text}\n"
                                        "CRITICAL RULE: You MUST call 'edit_file' immediately to fix this error!"
                                    )
                        except Exception:
                            # Safely ignore parsing issues if JSON or arguments are weird
                            pass

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
import flet as ft
def main(page: ft.Page):
    import flet as ft
    import os
    import json

    page.theme_mode = ft.ThemeMode.DARK
    page.title = "YF AI Private Code Writer"
    page.bgcolor = "#0B0C10"  # Sleek dark gray palette instead of raw black

    title = ft.Text(
        "Yamaan Faraz YF AI™",
        size=11,
        weight=ft.FontWeight.BOLD,
        color="#6C7A89"
    )

    chat_history = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
    )

    # Hardcoded to "guest" to match your send_click function exactly
    current_user_id = page.session.id

    filename = f"{CHAT_FILE}{current_user_id}"
    user_session_history = []

    # =========================================================================
    # 1. VISUAL HISTORY RELOADER ENGINE (Ensures it looks gorgeous on boot!)
    # =========================================================================
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                user_session_history = json.load(file)

            for message in user_session_history:
                raw_text = message.get("text", "")

                if raw_text.startswith("You:"):
                    # Clean out the prefix string for the UI display
                    clean_content = raw_text.replace("You:", "").strip()
                    chat_history.controls.append(
                        ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.PERSON, color=ft.Colors.BLUE_400, size=16),
                                ft.Text("You", color=ft.Colors.BLUE_200, weight=ft.FontWeight.W_600, size=13),
                            ], spacing=8),
                            ft.Row([
                                ft.VerticalDivider(width=24, color=ft.Colors.TRANSPARENT),
                                ft.Markdown(
                                    value=clean_content,
                                    selectable=True,
                                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                                    code_theme=ft.MarkdownCodeTheme.ATOM_ONE_DARK,
                                ),
                            ]),
                        ], spacing=4)
                    )
                elif raw_text.startswith("YF AI:"):
                    clean_content = raw_text.replace("YF AI:", "").strip()
                    chat_history.controls.append(
                        ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.SUPPORT_AGENT, color=ft.Colors.PURPLE_400, size=16),
                                ft.Text("YF AI", color=ft.Colors.PURPLE_200, weight=ft.FontWeight.W_600, size=13),
                            ], spacing=8),
                            ft.Row([
                                ft.VerticalDivider(width=24, color=ft.Colors.TRANSPARENT),
                                ft.Markdown(
                                    value=clean_content,
                                    selectable=True,
                                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                                    code_theme=ft.MarkdownCodeTheme.ATOM_ONE_DARK,
                                ),
                            ]),
                        ], spacing=4)
                    )
                # Append divider rules between loaded historical components
                chat_history.controls.append(ft.Divider(height=20, color=ft.Colors.GREY_800))
        except Exception as e:
            print(f"Error loading chat backup: {e}")
            user_session_history = []

    user_input = None
    send_btn = None


    # =========================================================================
    # 2. INTERACTIVE USER INPUT ANIMATION ENGINE
    # =========================================================================
    def handle_input_change(e):
        nonlocal user_input, send_btn
        if user_input and send_btn:
            has_text = bool(user_input.value.strip())
            btn_color = color_dropdown.value if ('color_dropdown' in locals() or 'color_dropdown' in globals()) and color_dropdown.value else "blue"
            send_btn.bgcolor = btn_color if has_text else "grey800"
            send_btn.opacity = 1.0 if has_text else 0.3
            send_btn.disabled = not has_text
            send_btn.update()

    # =========================================================================
    # 3. INTERACTIVE CHAT ENGINE WITH DUAL OVERRIDE VALUES
    # =========================================================================
    def send_click(e):
        nonlocal user_input, send_btn
        if not user_input or not user_input.value:
            return

        text_payload = user_input.value.strip()
        if not text_payload:
            return

        # Reload history to keep array states in sync before modifying
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as file:
                    current_history = json.load(file)
            except Exception:
                current_history = []
        else:
            current_history = []

        # 1. RENDER USER MESSAGE
        chat_history.controls.append(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, color=ft.Colors.BLUE_400, size=16),
                    ft.Text("You", color=ft.Colors.BLUE_200, weight=ft.FontWeight.W_600, size=13),
                ], spacing=8),
                ft.Row([
                    ft.VerticalDivider(width=24, color=ft.Colors.TRANSPARENT),
                    ft.Markdown(
                        value=text_payload, # <-- FIXED: Was throwing variable crash 'text' error here
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        code_theme=ft.MarkdownCodeTheme.ATOM_ONE_DARK,
                    ),
                ]),
            ], spacing=4)
        )

        current_history.append({"text": f"You: {text_payload}"})

        choosen_model = model_dropdown.value
        user_input.value = ""
        handle_input_change(None)
        page.update()

        try:
            cleaned_payload = clean_input_pipeline(text_payload)
            text = final_ai_agent(cleaned_payload, model=choosen_model, user_id=current_user_id)
            cloud_job_dispatched = dispatch_async_cloud_job(cleaned_payload, current_user_id)
            if not cloud_job_dispatched:
                print("failed to execute in cloud")
        except Exception as ex:
            text = f"An error occurred: {ex}"

        chat_history.controls.append(ft.Divider(height=10, color=ft.Colors.TRANSPARENT))

        # 2. RENDER AI RESPONSE
        chat_history.controls.append(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SUPPORT_AGENT, color=ft.Colors.PURPLE_400, size=16),
                    ft.Text("YF AI", color=ft.Colors.PURPLE_200, weight=ft.FontWeight.W_600, size=13),
                ], spacing=8),
                ft.Row([
                    ft.VerticalDivider(width=24, color=ft.Colors.TRANSPARENT),
                    ft.Markdown(
                        value=text,
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        code_theme=ft.MarkdownCodeTheme.ATOM_ONE_DARK,
                    ),
                ]),
            ], spacing=4)
        )

        chat_history.controls.append(ft.Divider(height=20, color=ft.Colors.GREY_800))

        ai_display = f"YF AI: {text}"
        current_history.append({"text": ai_display})

        # Save back safely to disk
        try:
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(current_history, file, ensure_ascii=False, indent=4)
        except Exception as write_err:
            print(f"err: {write_err}")

        page.update()

    # =========================================================================
    # 4. CAPSULE LAYOUT COMPONENT CONSTRUCTORS
    # =========================================================================
    send_btn = ft.IconButton(
        icon=ft.Icons.ARROW_UPWARD,
        icon_color="#0F0F11",  # Dark dark icon text creates stark premium contrast against gold
        bgcolor="#FFC107",  # Electric neon splash accent color
        disabled=True,
        opacity=0.4,
        width=44,
        height=44,
        on_click=send_click
    )

    user_input = ft.TextField(
        hint_text="Ask YF AI to do anything...",
        hint_style=ft.TextStyle(color="#3A3F47", size=13),
        text_style=ft.TextStyle(color=ft.Colors.WHITE, size=14),
        expand=True,
        multiline=True,
        max_lines=3,
        shift_enter=True,
        border_radius=30,
        border_color="#1F242E",
        focused_border_color="#4CC9F0",
        bgcolor="#141722",
        content_padding=ft.Padding(left=20, top=14, right=20, bottom=14),

        # FIX: Put this line back so the app watches your typing instantly!
        on_change=handle_input_change
    )

    input_row = ft.Row(
        controls=[
            user_input,
            send_btn
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=12,  # Space between the capsule input and the action button
    )

    app_content = ft.Column(
        controls=[
            ft.Row(controls=[title], alignment=ft.MainAxisAlignment.CENTER),
            chat_history,
            input_row,
        ],
        expand=True,
    )

        # =========================================================================
        # 5. MODULAR CONTROL DASHBOARD & SETTINGS OVERLAYS
        # =========================================================================

    def change_accent_color(e):
        selected_color = color_dropdown.value.lower()
        page.theme = ft.Theme(color_scheme_seed=selected_color)
        page.update()

    color_dropdown = ft.Dropdown(
        label="App Accent Theme Color",
        value="amber",
        options=[
            ft.dropdown.Option("amber", "Amber Gold"),
            ft.dropdown.Option("blue", "Deep Sea Blue"),
            ft.dropdown.Option("green", "Hacker Green"),
            ft.dropdown.Option("purple", "Cyber Neon Purple"),
        ],
        # Modern UI Styles (Capsule borders & deep inputs)
        border_radius=12,
        border_color="#222831",
        focused_border_color="#FFC107",
        bgcolor="#141722",
    )
    color_dropdown.on_change = change_accent_color

    # =========================================================================
    # MODERN MULTI-MODEL CONFIGURATION MATRIX
    # =========================================================================
    model_dropdown = ft.Dropdown(
        label="Target Language Model",
        value="openai/gpt-oss-120b",  # Ensured the initial value explicitly matches an available option
        options=[
            ft.dropdown.Option("openai/gpt-oss-120b", "GPT-OSS 120B (OpenAI)"),
            ft.dropdown.Option("openai/gpt-oss-20b", "GPT-OSS 20B (OpenAI)"),
            ft.dropdown.Option("minimaxai/minimax-m2.7", "MiniMax M2.7"),
        ],
        border_radius=12,
        border_color="#222831",
        focused_border_color="#FFC107",
        bgcolor="#141722",
    )

    # =========================================================================
    # FIXED & MODERNIZED CACHE PURGE SYSTEM
    # =========================================================================
    def wipe_chat_cache(e):
        # FIX: Changed '.set' to '.get' to prevent the multi-user crash.
        # It also cross-checks your session string format exactly!
        current_user_id = page.session.get("session_user_id") or "guest"
        target_path = f"chat_history_{current_user_id}.json"

        import os
        if os.path.exists(target_path):
            os.remove(target_path)

        # Clean the frontend visual view list immediately
        chat_history.controls.clear()
        settings_dialog.open = False
        page.update()

    # Modernized flat interactive layout actions
    clear_history_btn = ft.TextButton(
        "Wipe Chat Cache Context",
        icon=ft.Icons.DELETE_FOREVER,
        icon_color=ft.Colors.RED_400,
        style=ft.ButtonStyle(
            color=ft.Colors.RED_200,
            padding=ft.Padding(left=16, top=12, right=16, bottom=12),
            overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.RED_900)
        ),
        on_click=wipe_chat_cache
    )

    # =========================================================================
    # PREMIUM DIALOG SHEET CONTAINER
    # =========================================================================
    settings_dialog = ft.Column([
    # Page Header matching your ultra-modern style
    ft.Row([
        ft.Text("SYSTEM PARAMETERS", size=30, weight=ft.FontWeight.BOLD, color="#CA")
    ], alignment=ft.MainAxisAlignment.CENTER),
    ft.Divider(height=1, color="#1F232C"),

    # Description
    ft.Text(
        "Manage dashboard themes, assign core model target string paths, and purge session logs safely.",
        size=13, color="#6C7A89"
    ),
    ft.Divider(height=10, color="transparent"),

    # UI Appearance Section
    ft.Text("UI Appearance & Theme", size=13, weight=ft.FontWeight.W_600, color="#A7A9BE"),
    color_dropdown,  # Your existing dropdown

    ft.Divider(height=10, color="#1F232C"),

    # Model Configuration Section
    ft.Text("Model Configuration Layer", size=13, weight=ft.FontWeight.W_600, color="#A7A9BE"),
    model_dropdown,  # Your existing dropdown

    ft.Divider(height=10, color="#1F232C"),

    # Memory Actions Section
    ft.Text("System Memory Actions", size=13, weight=ft.FontWeight.W_600, color="#A7A9BE"),
    ft.Row([clear_history_btn], alignment=ft.MainAxisAlignment.START)
    ], expand=True, visible=False, spacing=12)


    # =========================================================================
    # THE REPLACEMENT SIDEBAR CONTROLLERS (Container Free)
    # =========================================================================
    # This button now anchors smoothly down on the left navigation drawer rail:
    # 1. Global storage and pipeline memory allocation variables
    image_history = []
    current_image_index = -1
    local_image_pipe = None  # Holds model in memory to prevent reloading

    # Text Input Field with fixed dimensions so Flet cannot crush it
    image_prompt_input = ft.TextField(
        hint_text="Describe the image you want to synthesize in the cloud...",
        hint_style=ft.TextStyle(color="#3A3F47", size=13),
        text_style=ft.TextStyle(color=ft.Colors.WHITE, size=14),
        expand=True,
        border_radius=30,
        border_color="#1F242E",
        focused_border_color="#FFC107",
        bgcolor="#141722",
        content_padding=ft.Padding(left=20, top=14, right=20, bottom=14),
    )

    # Main visual display widget with a stable local file placeholder setup
    ai_image_display = ft.Image(
        src="https://placehold.co",
        width=400,
        height=400,
        fit=ft.BoxFit.CONTAIN
,
        visible=True
    )
    header_row = ft.Row([ft.Text("YF AI", size=11, weight=ft.FontWeight.BOLD, color="#6C7A89")], alignment=ft.MainAxisAlignment.CENTER)

    # Define the Chat Pane layout column
    chat_pane = ft.Column([
        header_row,
        ft.Divider(height=1, color="#1F232C"),
        chat_history,
        input_row
    ], expand=True, spacing=16, visible=True) # Visible by default on launch

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
    import requests
    import time
    import flet_video as ftv

    # 2. LOCAL PIPELINE IMAGE GENERATION FUNCTION
    def run_image_generation(e):
        if not image_prompt_input.value.strip(): return
        submit_gen_btn.disabled = True
        loading_indicator.visible = True
        page.update()
        try:
            res = requests.post("https://huggingface.co", headers={"Authorization": "Bearer hf_TOKEN"},
                                json={"inputs": image_prompt_input.value.strip()})
            if res.status_code == 200:
                path = f"ai_image_{int(time.time())}.jpg"
                with open(path, "wb") as f: f.write(res.content)
                ai_image_display.src = path
                history_grid.controls.append(ft.Image(src=path, fit=ft.ImageFit.COVER, border_radius=8))
        except:
            pass
        finally:
            submit_gen_btn.disabled = False; loading_indicator.visible = False; page.update()

    image_prompt_input = ft.TextField(hint_text="Describe image...", expand=True, border_radius=30,
                                      border_color="#1F242E", focused_border_color="#FFC107", bgcolor="#141722",
                                      content_padding=ft.Padding(20, 14, 20, 14))
    ai_image_display = ft.Image(src="https://placehold.co", width=400, height=400, fit=ft.BoxFit.CONTAIN
)
    history_grid = ft.GridView(height=120, runs_count=5, max_extent=120, spacing=10, run_spacing=10)
    submit_gen_btn = ft.IconButton(ft.Icons.AUTO_AWESOME, icon_color="#0F0F11", bgcolor="#FFC107", width=44, height=44,
                                   on_click=run_image_generation)

    image_pane = ft.Column([
        ft.Row([ft.Text("IMAGE GENERATION", size=11, weight=ft.FontWeight.BOLD, color="#6C7A89")],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(height=1, color="#1F232C"),
        ft.Row([ai_image_display], alignment=ft.MainAxisAlignment.CENTER),
        loading_indicator,
        ft.Row([image_prompt_input, submit_gen_btn]),
        history_grid
    ], expand=True, visible=False, spacing=20)

    # =========================================================================
    # MINIMALIST VIDEO WORKSPACE
    # =========================================================================
    def generate_ltx_video(e):
        global video_url
        if not prompt.value.strip(): return
        submit_vid_btn.disabled = True
        loading_indicator.visible = True
        page.update()
        try:
            headers = {"Authorization": "Key YOUR_KEY", "Content-Type": "application/json"}
            req = requests.post("https://fal.run", headers=headers, json={"prompt": prompt.value.strip()}).json()
            if "request_id" not in req: return

            while True:
                chk = requests.get(f"https://fal.run{req['request_id']}", headers=headers).json()
                if "video" in chk: video_url = chk["video"]["url"]; break
                if chk.get("status") == "FAILED": return
                time.sleep(5)

            if video_url:
                os.makedirs("downloads", exist_ok=True)
                path = f"downloads/video_{req['request_id']}.mp4"
                with open(path, "wb") as f: f.write(requests.get(video_url).content)
                video_player.playlist = [ftv.VideoMedia(path)]
                video_player.update()
        except:
            pass
        finally:
            submit_vid_btn.disabled = False; loading_indicator.visible = False; page.update()

    prompt = ft.TextField(hint_text="Describe video...", expand=True, border_radius=30, border_color="#1F242E",
                          focused_border_color="#FFC107", bgcolor="#141722", content_padding=ft.Padding(20, 14, 20, 14))
    video_player = ftv.Video(height=450, playlist=[], fill_color=ft.Colors.BLACK, aspect_ratio=16 / 9, autoplay=True,
                             )
    submit_vid_btn = ft.IconButton(ft.Icons.VIDEO_CALL, icon_color="#0F0F11", bgcolor="#FFC107", width=44, height=44,
                                   on_click=generate_ltx_video)

    # 1. Remove expand=True from the core player constructor
    video_player = ftv.Video(
        playlist=[],
        fill_color=ft.Colors.BLACK,
        aspect_ratio=16 / 9,
        autoplay=True,
        # expand=True REMOVED FROM HERE
    )

    # 2. Keep expand=True on the parent pane, but wrap the player in ft.Expanded
    video_pane = ft.Column([
        ft.Row([
            ft.Text("VIDEO SYNTHESIZER", size=11, weight=ft.FontWeight.BOLD, color="#6C7A89")
        ], alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(height=1, color="#1F232C"),

        loading_indicator,
        ft.Row([prompt, submit_vid_btn], vertical_alignment=ft.CrossAxisAlignment.CENTER)
    ], expand=True, visible=False, spacing=20)  # KEEP expand=True here!

    # =========================================================================
    # SIDEBAR ROUTER (No Settings Modal)
    # =========================================================================
    def handle_nav_change(e):
        idx = e.control.selected_index
        chat_pane.visible = (idx == 0)
        image_pane.visible = (idx == 1)
        video_pane.visible = (idx == 2)
        settings_dialog.visible = (idx == 3)
        page.update()

    sidebar = ft.NavigationRail(
        selected_index=0, label_type=ft.NavigationRailLabelType.NONE, min_width=72, bgcolor="#111318",
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.CHAT_BUBBLE_OUTLINE, selected_icon=ft.Icons.CHAT_BUBBLE),
            ft.NavigationRailDestination(icon=ft.Icons.IMAGE_OUTLINED, selected_icon=ft.Icons.IMAGE),
            ft.NavigationRailDestination(icon=ft.Icons.VIDEOCAM_OUTLINED, selected_icon=ft.Icons.VIDEOCAM),
            ft.NavigationRailDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="Settings"),
        ],
        on_change=handle_nav_change
    )
    master_workspace = ft.Row([
        sidebar,
        ft.VerticalDivider(width=1, color="#1F232C"),
        ft.Stack([chat_pane, image_pane, video_pane, settings_dialog], expand=True)
    ], expand=True)

    page.add(master_workspace)

if __name__ == "__main__":

    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550)