import { useState, useEffect } from 'react';

// Haversine formula to calculate distance between two coordinates in km
function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371; // km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

export function useLocationServices() {
  const [location, setLocation] = useState(null);
  const [address, setAddress] = useState(null);
  const [nearestHospital, setNearestHospital] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    console.log("MedAgent: useLocationServices Hook Initialized");

    const fetchLocationData = async () => {
      try {
        if (!navigator.geolocation) {
          throw new Error("Geolocation is not supported by your browser");
        }

        console.log("MedAgent: Requesting Geolocation...");
        const position = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0
          });
        });

        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        console.log(`MedAgent: Location Found: ${lat}, ${lng}`);
        
        if (!isMounted) return;
        setLocation({ lat, lng, accuracy: position.coords.accuracy });

        // 1. Reverse Geocoding via Nominatim
        try {
          const nomRes = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`, {
            headers: { 'Accept-Language': 'en' }
          });
          if (nomRes.ok) {
            const nomData = await nomRes.json();
            if (isMounted) {
              setAddress(nomData.display_name);
              console.log(`MedAgent: Address Resolved: ${nomData.display_name}`);
            }
          }
        } catch (err) {
          console.warn("MedAgent: Reverse geocoding failed", err);
        }

        // 2. Nearest Hospital via Overpass API with Mirror Fallbacks
        const overpassMirrors = [
          'https://overpass-api.de/api/interpreter',
          'https://lz4.overpass-api.de/api/interpreter',
          'https://overpass.kumi.systems/api/interpreter'
        ];

        let overpassData = null;
        // Search for strictly hospitals within a larger radius but we will sort and pick the closest
        const query = `
          [out:json][timeout:20];
          (
            node["amenity"="hospital"](around:25000,${lat},${lng});
            way["amenity"="hospital"](around:25000,${lat},${lng});
            relation["amenity"="hospital"](around:25000,${lat},${lng});
          );
          out center;
        `;

        for (const mirror of overpassMirrors) {
          try {
            console.log(`MedAgent: Searching mirror ${mirror} for hospitals...`);
            const controller = new AbortController();
            const tId = setTimeout(() => controller.abort(), 12000); // 12s timeout
            const overpassRes = await fetch(mirror, {
              method: 'POST',
              body: query,
              signal: controller.signal
            });
            clearTimeout(tId);
            if (overpassRes.ok) {
              overpassData = await overpassRes.json();
              console.log(`MedAgent: Overpass Success from ${mirror}`);
              break; 
            }
          } catch (err) {
            console.warn(`MedAgent: Mirror ${mirror} failed`, err);
          }
        }

        // 3. Last Resort Fallback: Bounded Nominatim Search for "hospital"
        if (!overpassData || (overpassData.elements && overpassData.elements.length === 0)) {
          console.log("MedAgent: Overpass failed or empty, trying Nominatim hospital search...");
          try {
            const viewbox = `${lng-0.15},${lat+0.15},${lng+0.15},${lat-0.15}`;
            const searchRes = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=hospital&limit=10&lat=${lat}&lon=${lng}&viewbox=${viewbox}&bounded=1`);
            if (searchRes.ok) {
              const searchData = await searchRes.json();
              if (searchData && searchData.length > 0) {
                overpassData = { elements: searchData.map(item => ({
                  id: 'nom-' + item.place_id,
                  lat: parseFloat(item.lat),
                  lon: parseFloat(item.lon),
                  tags: { name: item.display_name.split(',')[0], 'addr:street': item.display_name.split(',').slice(1, 3).join(',').trim() }
                })) };
              }
            }
          } catch (e) {
            console.error("MedAgent: Nominatim fallback failed", e);
          }
        }
          
        if (overpassData && overpassData.elements && overpassData.elements.length > 0) {
          // Sort ALL elements by distance first
          const elements = overpassData.elements
            .map(el => {
              const elLat = el.lat || el.center?.lat;
              const elLng = el.lon || el.center?.lon;
              return { ...el, elLat, elLng, dist: elLat && elLng ? calculateDistance(lat, lng, elLat, elLng) : Infinity };
            })
            .filter(el => el.dist < 100) // Sanity check
            .sort((a, b) => a.dist - b.dist);

          if (elements.length > 0 && isMounted) {
            const closest = elements[0];
            const tags = closest.tags || {};
            const cleanName = tags.name || 'Nearby Hospital';
            
            // Smarter address construction
            const addrParts = [];
            if (tags['addr:street']) addrParts.push(tags['addr:street']);
            if (tags['addr:suburb']) addrParts.push(tags['addr:suburb']);
            if (tags['addr:city']) addrParts.push(tags['addr:city']);
            
            const hospitalAddr = addrParts.length > 0 ? addrParts.slice(0, 2).join(', ') : (tags.name || 'Local Medical Center');
            const arrivalMins = Math.round(closest.dist * 2 + 3);
            
            console.log(`MedAgent: Selected Closest: ${cleanName} at ${closest.dist.toFixed(2)}km`);
            
            setNearestHospital({
              id: closest.id || Date.now(),
              type: 'hospital',
              name: cleanName,
              details: hospitalAddr,
              phone: tags.phone || tags['contact:phone'] || null,
              distance: closest.dist < 1 ? `${(closest.dist * 1000).toFixed(0)}m` : `${closest.dist.toFixed(1)} km`,
              arrivalMinutes: arrivalMins,
              lat: closest.elLat,
              lng: closest.elLng
            });
          }
        }
        
        if (isMounted) setLoading(false);
      } catch (err) {
        console.error("MedAgent: useLocationServices Major Error:", err);
        if (isMounted) {
          setError(err.message || 'Failed to get location');
          setLoading(false);
        }
      }
    };

    fetchLocationData();

    return () => {
      isMounted = false;
    };
  }, []);

  return { location, address, nearestHospital, loading, error };
}
