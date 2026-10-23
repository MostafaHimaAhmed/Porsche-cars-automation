from rich.markup import escape
from rich import print 

def log(log_name, message, color=None):
    text = f"\\[{escape(str(log_name))}] {escape(str(message))}"
    print(f'[{color}]{text}[/{color}]' if color else text)