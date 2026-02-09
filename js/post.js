async function make_post(content) {
    const status = await fetch("/api/v1/post/create", {
        method: "POST",
        body: JSON.stringify({
            content: content
        }),
        headers: {
            "Authorization": `Bearer ${readCookie("twier_token")}`,
            "Content-Type": "application/json"
        }
    })

    return status
}
