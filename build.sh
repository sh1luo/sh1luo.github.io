rm -rf ./docs ./public &&
hugo && 
echo www.kcode.icu >> ./public/CNAME &&
mv public docs