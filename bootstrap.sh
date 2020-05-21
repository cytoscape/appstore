#!/usr/bin/env bash

# update apt database
apt-get update

# install base packages
apt-get -y install apache2 apache2-dev apache2-utils ssl-cert wget
apt-get -y install libapache2-mod-wsgi-py3 gcc g++
apt-get -y install mysql-server
apt-get -y install libjpeg8-dev
apt-get -y install geoip-database

# install miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod a+x Miniconda3-latest-Linux-x86_64.sh

./Miniconda3-latest-Linux-x86_64.sh -p /opt/miniconda3 -b
rm ./Miniconda3-latest-Linux-x86_64.sh

# set path to miniconda -- should really add to /etc/profile.d so everyone gets it
export PATH=/opt/miniconda3/bin:$PATH
echo "export PATH=/opt/miniconda3/bin:$PATH" >> /root/.bash_profile
echo "export PATH=/opt/miniconda3/bin:$PATH" >> /root/.bashrc
sudo -u vagrant echo "export PATH=/opt/miniconda3/bin:$PATH" >> /home/vagrant/.bash_profile

conda install -y -c conda-forge python-xapian


# install mod_wsgi
pip install mod_wsgi

# following mod_wsgi instructions found here:
# https://ostrokach.gitlab.io/post/apache-django-anaconda/
#

# update wsgi.conf configuration
WSGI_CONF="/etc/apache2/mods-available/wsgi.conf"
SITE_PKG=`find /opt/miniconda3 -regex "/opt/miniconda3/lib/python.*/site-packages$" -type d 2> /dev/null`
echo "<IfModule mod_wsgi.c>" > $WSGI_CONF
echo "   WSGIPythonHome /opt/miniconda3" >> $WSGI_CONF
echo "   WSGIPythonPath $SITE_PKG" >> $WSGI_CONF
echo "</IfModule>" >> $WSGI_CONF

# update wsgi.load file
mod_wsgi-express install-module | egrep "^LoadModule" > /etc/apache2/mods-available/wsgi.load

# enable wsgi
a2enmod wsgi

# build and install xapian

# XAPIAN_VERSION="1.4.15"
#XAPIAN_CORE="xapian-core-"
#wget https://oligarchy.co.uk/xapian/${XAPIAN_VERSION}/${XAPIAN_CORE}${XAPIAN_VERSION}.tar.xz
#unxz ${XAPIAN_CORE}${XAPIAN_VERSION}.tar.xz
#tar -xf ${XAPIAN_CORE}${XAPIAN_VERSION}.tar
#pushd ${XAPIAN_CORE}${XAPIAN_VERSION}
#./configure
#make
#make install
#popd
#rm -rf ${XAPIAN_CORE}${XAPIAN_VERSION}*

# updates shared library cache
ldconfig

# build and install xapian-bindings
#XAPIAN_BINDINGS="xapian-bindings-"
#wget https://oligarchy.co.uk/xapian/${XAPIAN_VERSION}/${XAPIAN_BINDINGS}${XAPIAN_VERSION}.tar.xz
#unxz ${XAPIAN_BINDINGS}${XAPIAN_VERSION}.tar.xz
#tar -xf ${XAPIAN_BINDINGS}${XAPIAN_VERSION}.tar
#pushd ${XAPIAN_BINDINGS}${XAPIAN_VERSION}
#./configure --with-python3
#make
#make install
#popd
#rm -rf ${XAPIAN_BINDINGS}${XAPIAN_VERSION}*

pip install -r /vagrant/requirements.txt

# TODO get app working properly
cd /var/www
mkdir CyAppStore
cd CyAppStore
cp -a /vagrant/* .

# Replace default site configuration
mv -f /etc/apache2/sites-available/000-default.conf /etc/apache2/sites-available/000-default.conf.orig
cp /vagrant/appstore.http.conf /etc/apache2/sites-available/000-default.conf
systemctl reload apache2

echo ""
echo "Visit http://localhost:8080"
