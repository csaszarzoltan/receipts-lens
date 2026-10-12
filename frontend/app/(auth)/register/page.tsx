import { redirect } from "next/navigation";

/** Creating a household starts with the email link: the first sign-in makes the household. */
export default function RegisterPage() {
  redirect("/auth/magic-link");
}
