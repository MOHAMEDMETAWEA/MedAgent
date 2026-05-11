export const prescriptions = [
  { id: 1, name: 'Lisinopril 10mg', type: 'Chronic Care', desc: 'ACE Inhibitor • Hypertension', freq: 'Daily', time: 'Morning • 08:00 AM', status: 'completed', category: 'primary' },
  { id: 2, name: 'Metformin 500mg', type: 'Metabolic', desc: 'Antidiabetic • Type 2', freq: '2x Day', time: 'Noon • 01:00 PM', status: 'pending', category: 'tertiary' },
  { id: 3, name: 'Atorvastatin 20mg', type: 'Statins', desc: 'Lipid-lowering • Cholesterol', freq: 'Nightly', time: 'Evening • 09:00 PM', status: 'scheduled', category: 'secondary' },
];

export const doctors = [
  { id: 1, name: 'Dr. Julian Vane', specialty: 'Senior Cardiologist', status: 'ONLINE', rating: '4.9', exp: '12 years exp.', gender: 'M', avatarUrl: null },
  { id: 2, name: 'Dr. Sarah Jenkins', specialty: 'Neurology Specialist', status: 'BUSY', rating: '5.0', exp: '8 years exp.', gender: 'F', avatarUrl: null },
  { id: 3, name: 'Dr. Maya Patel', specialty: 'Pediatric Specialist', status: 'ONLINE', rating: '4.8', exp: '15 years exp.', gender: 'F', avatarUrl: null },
  { id: 4, name: 'Dr. Liam Chen', specialty: 'General Practitioner', status: 'OFFLINE', rating: '4.7', exp: '5 years exp.', gender: 'M', avatarUrl: null }
];

export const scanHistory = [
  { id: 1, type: 'Chest X-Ray / Post-Op', status: 'Completed', details: 'Analyzed Oct 24, 2023 • 14.2 MB DICOM', insights: ['AI Insight: Normal Lung Expansion', 'Verified by Dr. Aris'], imgUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuABc1Llg7jPsb0VMTv5PcCEqJmFmRkk0PE3JkXCmgrL0kmvIRAyA7tf-_oH38Fxu7PF-u3sPzYEkqudeYDB0iUuZJhnpPU8yeX8S5cEmNvAdb7ec98TCJJ5dknn6UmTN_dVnuwrZZViMWMuGkuoDx9GN85E_0Ncx2zJZSE2M1JeSPV78lcOtGgG0fTon9AKulQQo4I-EFl3DKYH5akxsuXTZktv5K2hFK0KOXYngYVsrGkruX4tIH66WZAW8SsBP2MhYUHt-A_vFI2-' },
  { id: 2, type: 'Head MRI / Routine', status: 'Processing', details: 'Analyzed Oct 21, 2023 • 88.5 MB DICOM', insights: [], imgUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDCtEmAekhz5gLd9HthE6VcfB2cLl2rfOZsxvaVFJv3eMwycF1DfsLOMR9evGq6vxKcy4zro44Ig_U60pC0zuF71ZRJO1hGxK8ETLsUaxGFQGCU5ACOHcWQhQzGV612O_GS4TwbqfUzOwI_4j2cnkW-fSIuokiFk5AC-SC6moWcw7NGScGTdnuF1ikVh08JQ0opJ-Y5teMEq2YbW4QO4nGk8SsYlUIiaXQeJ1be0weIupKSjPWEEYxRzcVJmUzE-hrUQ9RbXbrmgE9g' },
  { id: 3, type: 'Lumbar Spine / L4-L5', status: 'Anomaly Detected', details: 'Analyzed Oct 15, 2023 • 22.1 MB DICOM', insights: ['AI Insight: L4-L5 Compression Noted', 'Urgent Review Requested'], imgUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDV6NJnoTMWnq3Qo5-nFZ6KGyO7U85apjZqj6ds7IDVn1To00b4eCl2c0IqqPpUofFVr_5Xa42ol1x4cpJhUFDTgHLTMkdj4VdcWpSRJJ2euPzBQBUnVhmPrI0DerRxhyJrKLWzltBc_6Wavqx5Y66UW-aErxVktLyNBl8ujVqOGtUBe0RyMY_MxTjwpaqIuippk4GtTkNs9gw1XFH9qt3R5JztGH4UIdIEoB7Z5uAsjTYkt_VYmp2OeoWJ5aNK_sC0lHSPWB5yk9GH' }
];

export const emergencyFacilities = [
  { id: 1, name: 'City General Hospital', distance: '2.4 km', details: 'Level 1 Trauma Center • Open 24/7', type: 'hospital' },
  { id: 2, name: 'Private Ambulance Service', distance: 'Fastest', details: 'Estimated arrival: 8-12 mins', type: 'ambulance' },
];

export const chatHistory = [
  { id: 1, text: "Hello Alex. I've analyzed your most recent ECG results and noted a slight variation in your resting heart rate. How have you been feeling today? Have you experienced any dizziness or shortness of breath?", sender: 'ai', tags: ['Analysis Active', '98% Confidence'] },
  { id: 2, text: "I felt some minor tightness in my chest this morning while climbing the stairs, but it subsided after resting for five minutes.", sender: 'user', time: 'Read 10:42 AM' },
  { id: 3, text: "Thank you for sharing that. I've cross-referenced this with your last lab work. I've prepared a specialized Lab Analysis report based on your symptoms. Please review the attached file.", sender: 'ai', file: { name: 'Lab_Analysis_Report_CE9921.pdf', desc: '2.4 MB • Analysis Report' } }
];

export const emergencyContacts = [];
