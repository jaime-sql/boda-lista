export interface ScheduleItem {
  time: string;
  activity: string;
}

export interface WeddingContact {
  role: string;
  phone: string;
}

export interface WeddingInfo {
  event_name: string;
  partners: string[];
  date: string;
  schedule: ScheduleItem[];
  dress_code: string;
  venue: {
    name: string;
    address: string;
    notes: string;
  };
  parking: string;
  gifts: string;
  contacts: WeddingContact[];
}
