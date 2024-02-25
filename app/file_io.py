import os

import aiofiles


async def store_files(images):
    paths = []
    for image in images:
        out_file_path = os.path.join(os.getcwd(), "resources", image.filename)
        async with aiofiles.open(out_file_path, 'wb') as out_file:
            content = await image.read()
            await out_file.write(content)
        paths.append(out_file_path)
    return ",".join(paths)
