def indent(x):
    return''.join(["  " for i in range(x)])

def XML_dump(body, ind=0):
    lines = []
    for key in body:
        if type(body[key]) == type(list()):
            for item in body[key]:
                lines.append(XML_dump({key: item}, ind + 1))
            continue
        lines.append("%s<%s>" % (indent(ind), key))
        if type(body[key]) == type(dict()):
            lines.append(XML_dump(body[key], ind + 1))
        else:
            lines.append("%s%s" % (indent(ind + 1), body[key]))
        lines.append("%s</%s>" % (indent(ind), key))
    return '\n'.join(lines)
