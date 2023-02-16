def format_title(odic: dict, max_len_line: int = 60) -> str:
    txt = ""
    last_line = 0
    for key, value in odic.items():
        new_txt = key + " = " + str(value)
        if last_line + len(new_txt) < max_len_line:
            txt += ("; " if txt != "" else "") + new_txt
            last_line += len(new_txt) + 2
        else:
            last_line = len(new_txt)
            txt += "\n" + new_txt
    return txt
