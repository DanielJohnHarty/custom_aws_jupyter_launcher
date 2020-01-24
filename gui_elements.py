import tkinter
from tkinter import filedialog

FILETYPES = [
            ("All Files", ("*.*")),
            ("Launched AWS Instances", "*.aws")
            ]

def tkinter_build_and_teardown(func):
    """
    Decorator which creates a tkinter root
    instance and hides it before calling the function.
    The tkinter instance is destroyed immediately after execution.
    """
    def wrapped_tkinter_call():
        try:
            root = tkinter.Tk()
            root.iconbitmap(r'imgs\AWS.ico')
            root.wm_withdraw()
            return func()
        except:
            pass
        finally:
            root.destroy()

    return wrapped_tkinter_call

@tkinter_build_and_teardown
def get_system_filepath():
    """
    Returns the selected filepath.
    """
    filename = filedialog.askopenfilename(filetypes=FILETYPES)
    return filename

@tkinter_build_and_teardown
def get_save_as_filepath():
    """
    Returns the selected filepath and warns if
    would lead to overwriting a file.
    """
    filename = filedialog.asksaveasfilename(filetypes=FILETYPES)
    return filename
