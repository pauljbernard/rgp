"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

const sessionCookieName = "rgp_access_token";
const authStateCookieName = "rgp_auth_state";

export async function logoutAction() {
  const store = await cookies();
  store.delete(sessionCookieName);
  store.delete(authStateCookieName);
  redirect("/login");
}
