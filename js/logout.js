// requires: cookie.js

// preforms logout
async function logout() {
    await fetch("/api/v1/session/logout", {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${readCookie("twier_token")}`
        }
    });
    eraseCookie("twier_token")

    window.location = "/"
}
