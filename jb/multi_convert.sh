for dir in 20*
do 
	cd $dir
	for file in *.ipynb
	do
		
		python ../../../plotly-converter/myst-converter.py $file
	done
	cd ..
done