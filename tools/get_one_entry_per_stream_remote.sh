keys=`redis-cli KEYS \* | awk '{print $2}' | tr -d '"' | tr -d '\n'`
for key in $keys
do
    echo "oc rsh $host redis-cli -c XRANGE $key - + COUNT 1"
done
