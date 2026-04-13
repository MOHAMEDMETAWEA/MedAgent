const fs = require('fs');

const updateJson = (path, newKeys) => {
  const content = JSON.parse(fs.readFileSync(path, 'utf8'));
  
  Object.keys(newKeys).forEach(ns => {
    if (!content[ns]) content[ns] = {};
    content[ns] = { ...content[ns], ...newKeys[ns] };
  });

  fs.writeFileSync(path, JSON.stringify(content, null, 2));
};

updateJson('./src/i18n/locales/en.json', {
  scans: {
    title: "Scan Imaging",
    subtitle: "Upload your X-Ray, MRI, or CT scans for instant AI-assisted diagnostic insights. MedAgent utilizes deep neural networks to identify anomalies with 99.4% precision.",
    drop: "Drop your medical scans here",
    support: "Support for DICOM, JPEG, and PNG formats. Maximum file size: 124MB per study.",
    select: "Select Medical Files",
    engine: "Ether AI Engine",
    processing: "Processing v4.2 Active",
    avg: "Avg. Analysis",
    recent: "Recent Analysis History",
    viewAll: "View All Archives"
  },
  emergency: {
    title: "Emergency Center",
    subtitle: "Help is nearby. Activate SOS for immediate broadcast or select a dedicated service below.",
    urgent: "Urgent Assistance Mode",
    sosHold: "Hold to activate",
    activating: "Activating SOS will:",
    call911: "Call 911",
    liveLoc: "Send Live Location",
    guardians: "Alert 3 Guardians",
    quickContacts: "Quick Contacts",
    nearby: "Nearby your location",
    directions: "Directions",
    currentLoc: "Current Location Data",
    essentialId: "Essential Medical ID"
  }
});

updateJson('./src/i18n/locales/ar.json', {
  scans: {
    title: "الأشعة وتفاصيل الصور",
    subtitle: "قم بتحميل صور الأشعة السينية، الرنين المغناطيسي، أو المقطعية للحصول على تحليل ذكي فوري. يستخدم النظام شبكات عصبية عميقة لاكتشاف التشوهات بدقة 99.4٪.",
    drop: "اسحب صور الأشعة هنا",
    support: "يدعم صيغ DICOM، JPEG، و PNG. الحد الأقصى لحجم الملف: 124 ميجابايت.",
    select: "تحديد الملفات الطبية",
    engine: "محرك إيثر للذكاء الاصطناعي",
    processing: "المعالجة الإصدار 4.2 نشط",
    avg: "متوسط التحليل",
    recent: "سجل التحليلات الحديثة",
    viewAll: "عرض كافة الأرشيفات"
  },
  emergency: {
    title: "مركز الطوارئ",
    subtitle: "المساعدة قريبة. قم بتفعيل نداء الاستغاثة للبث الفوري للموقع أو اختر خدمة مخصصة بالأسفل.",
    urgent: "وضع المساعدة العاجلة",
    sosHold: "اضغط مطولاً للتفعيل",
    activating: "تفعيل الاستغاثة سيقوم بـ:",
    call911: "الاتصال بـ 911",
    liveLoc: "إرسال الموقع المباشر",
    guardians: "تنبيه 3 حراس",
    quickContacts: "جهات الاتصال السريعة",
    nearby: "بالقرب من موقعك",
    directions: "الاتجاهات",
    currentLoc: "بيانات الموقع الحالي",
    essentialId: "الهوية الطبية الأساسية"
  }
});
console.log("JSON dicts updated via explicit merging!");
