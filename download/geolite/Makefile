all: GeoLiteCity.dat GeoIP.dat
	date > last_updated

GeoLiteCity.dat:
	wget http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz
	gunzip GeoLiteCity.dat.gz

GeoIP.dat:
	wget http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz
	gunzip GeoIP.dat.gz

clean:
	rm -f last_updated GeoLiteCity.dat GeoIP.dat
