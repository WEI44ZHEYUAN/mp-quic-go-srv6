rm result.log
rm test.log

for i in {1..10}; do

    (time ./main -m -c https://[fc00:3::2]:6121/ramdisk/random) 2>&1 | tee -a test.log
    rm cache*

    sleep 40
done

cat test.log | grep real | awk '{print $2}' >> result.log