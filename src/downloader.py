import asyncio
import aiohttp
import aiofiles
import signal
from pathlib import Path
from config.settings import HEADERS, COOKIES, PDF_DIR, MAX_WORKERS


class AsyncPDFDownloader:
    def __init__(self, reg_no_list: list[str], max_concurrent_tasks=MAX_WORKERS):
        self.reg_no_list = reg_no_list
        self.max_concurrent_tasks = max_concurrent_tasks
        self.failed_reg_ids = []
        self.failure_reasons = []
        self.stop_signal = False

    def _handle_signals(self):
        def handler(_sig_num, _frame):
            print("\n[!] Received interrupt signal. Stopping gracefully...")
            self.stop_signal = True

        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)

    @staticmethod
    async def _download_file(session: aiohttp.ClientSession, reg_no: str, file_type: str, filename: Path):
        if file_type == "registration":
            url = f"https://foscos.fssai.gov.in/gateway/downloadpdf2/registration/{reg_no}"
        elif file_type == "application":
            url = f"https://foscos.fssai.gov.in/gateway/fbo_readonly/getlogintofortacereg/{reg_no}"
        else:
            raise ValueError("Unknown file_type")

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    filename.parent.mkdir(parents=True, exist_ok=True)
                    async with aiofiles.open(filename, "wb") as f:
                        await f.write(content)
                else:
                    raise Exception(f"Status: {response.status}, URL: {url}")
        except Exception as e:
            raise e

    async def _download_for_single_reg(self, reg_no: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore):
        async with semaphore:
            if self.stop_signal:
                return
            try:
                await self._download_file(session, reg_no, "registration", PDF_DIR / f"registration_{reg_no}.pdf")
                await self._download_file(session, reg_no, "application", PDF_DIR / f"application_form_{reg_no}.pdf")
            except Exception as e:
                print(f"[FAILED] Both PDFs for Reg ID {reg_no} - {e}")
                self.failed_reg_ids.append(reg_no)
                self.failure_reasons.append(str(e))

    async def download_all(self):
        self._handle_signals()
        connector = aiohttp.TCPConnector(limit=100)
        cookie_jar = aiohttp.CookieJar()
        for name, value in COOKIES.items():
            cookie_jar.update_cookies({name: value})

        timeout = aiohttp.ClientTimeout(total=None)  # No global timeout
        semaphore = asyncio.Semaphore(self.max_concurrent_tasks)

        async with aiohttp.ClientSession(headers=HEADERS, cookie_jar=cookie_jar, connector=connector,
                                         timeout=timeout) as session:
            tasks = []
            for i, reg_no in enumerate(self.reg_no_list, 1):
                if self.stop_signal:
                    break
                task = self._download_for_single_reg(reg_no, session, semaphore)
                tasks.append(asyncio.create_task(task))
                if i % 50 == 0:
                    print(f"[INFO] Submitted {i} download tasks...")

            await asyncio.gather(*tasks)

        if self.failed_reg_ids:
            print(f"\n[SUMMARY] Total Failed Registration IDs: {len(self.failed_reg_ids)}")
            for reg_id in self.failed_reg_ids:
                print(f" - {reg_id}")
            unique_errors = set(self.failure_reasons)
            print(f"\n[SUMMARY] Unique Error Reasons ({len(unique_errors)}): ")
            for reason in unique_errors:
                print(f"- {reason}")
