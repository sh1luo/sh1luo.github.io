rm -rf ./public ./docs && 
hugo &&
echo kcode.icu >> ./public/CNAME && 
mv public docs