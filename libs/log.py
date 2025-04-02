import inspect

PRINT_LOG = False

CRED = "\033[38;5;196m"
CGREEN = "\033[38;5;46m"
CBLUE="\033[38;5;39m"
CORANGE="\033[38;5;208m"

COK = CGREEN
CKO = CRED
CWARN = "\033[38;5;214m"
CERROR = CRED
CRST = "\033[0m"

def get_caller():
    frame = inspect.currentframe()
    caller_frame = frame.f_back
    
    if caller_frame is not None:
        caller_of_caller_frame = caller_frame.f_back
        if caller_of_caller_frame is not None:
            if caller_of_caller_frame.f_back is not None:
                return f"{caller_of_caller_frame.f_back.f_code.co_name}.{caller_of_caller_frame.f_code.co_name}"
            return caller_of_caller_frame.f_code.co_name
    return None

def printl(msg):
    global PRINT_LOG
    if PRINT_LOG:
        print(f"{CBLUE}[{get_caller()}]{CORANGE}<INFO> :{CRST} {msg}", flush=True)

def warnl(msg):
    global CWARN
    print(f"{CBLUE}[{get_caller()}]{CWARN}<WARN> : {msg}{CRST}", flush=True)

def exitl(msg):
    global CERROR
    print(f"{CBLUE}[{get_caller()}]{CERROR}<ERROR> : {msg}{CRST}", flush=True)
    exit(1)