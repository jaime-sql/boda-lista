export interface PersonName {
  first_name: string;
  last_name: string;
}

export interface ScheduleItem {
  time: string;
  title: string;
  place?: string;
  notes?: string;
}

export interface InfoBlock {
  summary: string;
  details?: string;
  notes?: string;
}

export interface WeddingContact {
  name: string;
  role: string;
  email?: string;
  phone?: string;
}

export interface WeddingInfo {
  synthetic: true;
  disclaimer: string;
  couple: {
    bride: PersonName;
    groom: PersonName;
  };
  date: string;
  timezone: string;
  schedule: ScheduleItem[];
  venue: {
    name: string;
    address: string;
    city: string;
    country: string;
    ceremony_area?: string;
    reception_area?: string;
    notes?: string;
  };
  dress_code: InfoBlock;
  parking: InfoBlock;
  gifts: InfoBlock;
  contacts: WeddingContact[];
}
