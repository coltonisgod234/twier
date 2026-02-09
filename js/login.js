async function login(username, password) {
    const resp = await fetch(`/api/v1/users/${username}/login`, {
        method: "POST",
        body: JSON.stringify({
            passwd: password
        }),
        headers: {
            "Content-Type": "application/json"
        }
    });

    return resp
}

async function do_website_login(username, passwd) {
    let r = await login(username, passwd);

    let status = r.status;
    let jso = await r.json();
    let error = jso.error;

    if (status != 200) {
        document.writeln(`error during login, ${status}: "${error}"`)
    } else {
        window.location = "/"
    }

    let token = jso.token;

    // token lasts one week
    createCookie("twier_token", token, 7);
}
