import tkinter
from tkinter import messagebox, filedialog

SAVED_FILE_EXTENTION = ".aws"
FILETYPES = [
            
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
def get_saved_file_filepath():
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
    filename = filename + SAVED_FILE_EXTENTION if not filename.endswith(SAVED_FILE_EXTENTION) else filename
    return filename

@tkinter_build_and_teardown
def confirm_save():
    to_save = messagebox.askokcancel("Question","Save your launched instance details?")
    return to_save
