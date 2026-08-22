import client from "./client";

// Backend expects OAuth2PasswordRequestForm — form-encoded, field name
// "username" (not JSON, not "email") — see backend/app/routers/auth.py.
export async function login({ email, password }) {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);

  const { data } = await client.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data; // { access_token, token_type }
}

// role is required by UserCreate: "doctor" | "nurse" | "records_staff" | "admin"
export async function register({ name, email, password, role }) {
  const { data } = await client.post("/auth/register", { name, email, password, role });
  return data;
}
