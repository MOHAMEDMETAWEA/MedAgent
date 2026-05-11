/**
 * Dictionary mapping Country Codes (ISO 3166-1 alpha-2) to local Emergency Ambulance numbers.
 * Fallback is 112, the GSM standard worldwide emergency number.
 */

export const emergencyNumbers = {
  // Global / North America
  us: '911',
  ca: '911',
  mx: '911',
  ph: '911',
  
  // Europe / General (112 is standard, but mapping for clarity)
  gb: '999', // UK
  de: '112', // Germany
  fr: '15',  // France
  ru: '103', // Russia (Ambulance)

  // Arab Countries
  sa: '997', // Saudi Arabia (Ambulance)
  ae: '998', // UAE (Ambulance)
  eg: '123', // Egypt (Ambulance)
  ma: '15',  // Morocco
  bh: '999', // Bahrain
  iq: '122', // Iraq
  kw: '112', // Kuwait
  om: '112', // Oman

  // APAC / Others
  au: '000', // Australia
  nz: '111', // New Zealand
  jp: '119', // Japan
  in: '102', // India
  br: '192', // Brazil
};

/**
 * Retrieves the standard emergency number based on ISO country code.
 * @param {string} countryCode - ISO 3166-1 alpha-2 lower-cased
 * @returns {string} - The emergency phone number
 */
export const getEmergencyNumber = (countryCode) => {
  if (!countryCode) return '122';
  return emergencyNumbers[countryCode.toLowerCase()] || '122';
};
