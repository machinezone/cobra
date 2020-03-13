"""Small tool to edit cobra app config relatively easily
"""

import os
import yaml

cmd = "oc get -o yaml dc/cobra | grep -A 1 'name: COBRA_APPS_CONFIG_CONTENT' "
cmd += " | tail -n 1 | awk -F: '{print $2}'"
value = os.popen(cmd).read()

pid = os.getpid()
tmpFile = f'/tmp/oc-{pid}.value'

# that step is maybe to
with open(tmpFile, 'w') as f:
    f.write(value.strip())

yamlContent = os.popen(f'cat {tmpFile} | base64 -D | gunzip -c').read()

tmpFile = f'/tmp/oc-{pid}.yaml'
with open(tmpFile, 'w') as f:
    f.write(yamlContent)

os.system(f'vi {tmpFile}')

# that step is maybe to
with open(tmpFile) as f:
    data = yaml.load(yamlContent, Loader=yaml.FullLoader)

os.system(f'cat {tmpFile} | gzip -c | base64 | pbcopy')
print('oc edit dc/cobra')
print('grep for COBRA_APPS_CONFIG_CONTENT now')
