rm -rf ./public ./docs && 
hugo &&
echo kcode.icu >> ./public/CNAME && 
mv public docs &&
git add . && 
git commit -m "update blog..." &&
git push origin master