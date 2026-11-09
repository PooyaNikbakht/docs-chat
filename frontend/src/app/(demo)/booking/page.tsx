import type { Metadata } from "next";
import { BookingDemo } from "@/components/demo/BookingDemo";

export const metadata: Metadata = {
  title: "Booking receptionist",
  description:
    "A website chat that checks open appointment times, offers them as buttons and books one after the visitor confirms.",
};

export default function BookingPage() {
  return <BookingDemo />;
}
