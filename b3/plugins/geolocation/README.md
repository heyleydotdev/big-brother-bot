Geolocation Plugin for BigBrotherBot
====================================

Description
-----------
A [BigBrotherBot][B3] plugin which introduces geolocation capabilities. This plugin is meant to be used as subplugin 
since it doesn't provide commands or visual reaction to B3 events. The plugin intercepts new clients connection and
retrieve geolocation data using multiple data sources (tried in order until one succeeds):

* a local MaxMind DB file, tried first: [DB-IP Lite City](https://db-ip.com/db/download/ip-to-city-lite) or
  [GeoLite2 City](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data) *(recommended)*
* [IP api](http://ip-api.com/)
* [IP WhoIs](https://ipwho.is/)
* [Free IP API](https://freeipapi.com/)

### Local database setup

A local database is tried before the HTTP services: no network round trip for the players it knows, no rate limit,
and no player IP sent to a third party.

1. Download the free DB-IP Lite City database (CC BY 4.0, updated monthly) from
   <https://download.db-ip.com/free/dbip-city-lite-YYYY-MM.mmdb.gz> and extract the `.mmdb` file. A GeoLite2 City
   `.mmdb` file works too, it uses the same schema. The Country editions also work but hold no city, region,
   coordinates nor time zone, so `!location` and `!distance` lose those values.
2. Put it in `b3/plugins/geolocation/db/` as `dbip-city-lite.mmdb` (or `GeoLite2-City.mmdb`). The same file names are
   also looked up in `/usr/local/share/GeoIP/` and `/usr/share/GeoIP/`.

The database is re-read on every B3 start: replace the file to update the data. No local database provides an ISP
name, so `client.location.isp` stays empty for the players answered from the file. When redistributing or displaying
the data, DB-IP asks for the attribution "IP Geolocation by [DB-IP](https://db-ip.com)".

Retrieved geolocation data is cached per ip address for 24 hours: reconnecting players won't generate new requests
and the same client is never geolocated by two events at the same time.

For plugin developers
---------------------
To notify other plugins of client geolocation being completed, two events are being fired:

* `EVT_CLIENT_GEOLOCATION_SUCCESS` : when the geolocation succeeds
* `EVT_CLIENT_GEOLOCATION_FAILURE` : when the geolocation fails

When the geolocation succeed a new attribute is added the the `b3.clients.Client` object: `location`. This attribute
will hold all the geolocation data the plugin could retrieve:
 
* `client.location.country` : the country name
* `client.location.region` : the region name
* `client.location.city` : the city name
* `client.location.cc` : the two letter country code
* `client.location.rc` : the two letter region code
* `client.location.isp` : the Internet Service Provider name
* `client.location.lat` : the latitude value
* `client.location.lon` : the longitude value
* `client.location.timezone` : the timezone string
* `client.location.zipcode` : the postal code

*NOTE #1* : when `EVT_CLIENT_GEOLOCATION_FAILURE` is fired `client.location` is set to `None`  
*NOTE #2* : when the plugin cannot retrieve a specific geolocation value, its attribute is set to `None`