rm -rf ./public ./docs &&
hugo && 
echo www.kcode.icu >> ./public/CNAME && 
mv public docs