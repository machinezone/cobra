
with open('DOCKER_VERSION') as f:
    version = f.read()

with open('DOCKER_VERSION', 'w') as f:
    major, minor, patch = version.split('.')
    patch = int(patch) + 1
    f.write('{}.{}.{}\n'.format(major, minor, patch))
