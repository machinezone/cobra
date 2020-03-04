import hiredis


def convertResponse(response, cmd):
    # We need special handling for redis reply errors
    responseType = type(response)
    if responseType == hiredis.ReplyError:
        return response

    if cmd == 'INFO':
        s = response.decode()

        attributes = {}
        for line in s.splitlines():
            if line.startswith('#'):
                continue

            key, _, val = line.partition(':')
            attributes[key] = val

        return attributes

    elif cmd == 'XREAD':
        items = []
        for item in response[0][1]:
            position = item[0]
            array = item[1]
            entries = {}

            for i in range(len(array) // 2):
                key = array[2 * i]
                value = array[2 * i + 1]
                entries[key] = value

            items.append((position, entries))
        return {response[0][0]: items}

    elif cmd == 'XREVRANGE':
        items = []
        for item in response:
            position = item[0]
            array = item[1]
            entries = {}

            for i in range(len(array) // 2):
                key = array[2 * i]
                value = array[2 * i + 1]
                entries[key] = value

            items.append((position, entries))

        return items
    else:
        return response
