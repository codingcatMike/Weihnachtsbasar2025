import random
import string
import csv
import json
from pathlib import Path
from importlib import import_module

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model, authenticate
from django.test import Client, RequestFactory
from django.db.models import Q
import tkinter as tk
from tkinter import messagebox

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Create demo users with flexible password, staff/superuser flags, "
        "login test, preview, output formats, password reset, and GUI mode"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "usernames", nargs="+", type=str,
            help="One or more base usernames (e.g., Demo1 Demo2) or 'gui' to open GUI"
        )
        parser.add_argument("--password", type=str, help="Password (default from settings or 'demo')")
        parser.add_argument("--gp", nargs="?", const=None, type=int,
                            help="Generate random password (optional length)")
        parser.add_argument("--count", type=int, default=None,
                            help="Number of users to create per base username (default from settings or 1)")
        parser.add_argument("--same-pass", action="store_true", help="All users get same password")
        parser.add_argument("--staff", action="store_true", help="User is staff")
        parser.add_argument("--superuser", action="store_true", help="User is superuser")
        parser.add_argument("--skip-pw-check", action="store_true", help="Skip login test")
        parser.add_argument("--sf", action="store_true", help="Show preview first")
        parser.add_argument("--skip", choices=["fill", "end", "mixed"], default="fill",
                            help="How to fill gaps in numbering")
        parser.add_argument("--output", nargs="+", choices=["none", "txt", "csv", "json", "bat"],
                            default=None, help="Output format (add 'dev' or 'user' after type)")
        parser.add_argument("--modify", type=str,
                            help="Modify existing users: e.g., pw=NEW,email=x@x.com")
        parser.add_argument("--delete", action="store_true", help="Delete all matching users")
        parser.add_argument("--logintest", nargs="?", const="normal",
                            choices=["normal", "admin", "both"],
                            help="Test login (normal, admin, or both)")
        parser.add_argument("--visiturl", type=str,
                            help="Visit a given URL as the user after login")
        parser.add_argument("--runview", type=str, help="Run a view function directly (dotted path)")
        parser.add_argument("--form", nargs="+",
                            help="Submit a form: first arg is URL, rest are key=value pairs")

    # ---------------- GUI MODE ----------------
    def run_gui(self):
        root = tk.Tk()
        root.title("Demo User Manager GUI")

        # Variables
        username_var = tk.StringVar(value="Demo")
        pw_var = tk.StringVar(value="demo")
        count_var = tk.StringVar(value="1")
        staff_var = tk.BooleanVar()
        su_var = tk.BooleanVar()
        gp_var = tk.BooleanVar()

        # Layout
        tk.Label(root, text="Base Username:").grid(row=0, column=0, sticky="w")
        tk.Entry(root, textvariable=username_var).grid(row=0, column=1)

        tk.Label(root, text="Password:").grid(row=1, column=0, sticky="w")
        tk.Entry(root, textvariable=pw_var, show="*").grid(row=1, column=1)

        tk.Label(root, text="Count:").grid(row=2, column=0, sticky="w")
        tk.Entry(root, textvariable=count_var).grid(row=2, column=1)

        tk.Checkbutton(root, text="Staff", variable=staff_var).grid(row=3, column=0)
        tk.Checkbutton(root, text="Superuser", variable=su_var).grid(row=3, column=1)
        tk.Checkbutton(root, text="Generate Password", variable=gp_var).grid(row=4, column=0, columnspan=2)

        # Buttons
        def create_users():
            try:
                self.handle(
                    usernames=[username_var.get()],
                    password=pw_var.get(),
                    gp=10 if gp_var.get() else None,
                    count=int(count_var.get()),
                    same_pass=True,
                    staff=staff_var.get(),
                    superuser=su_var.get(),
                    skip_pw_check=False,
                    sf=False,
                    skip="fill",
                    output=None,
                    modify=None,
                    delete=False,
                    logintest=None,
                    visiturl=None,
                    runview=None,
                    form=None,
                )
                messagebox.showinfo("Success", "Users created successfully!")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(root, text="Create Users", command=create_users).grid(row=5, column=0, columnspan=2, pady=5)
        root.mainloop()

    # ---------------- MAIN HANDLE ----------------
    def handle(self, *args, **options):
        usernames = options.get("usernames") or ["Demo"]

        # Launch GUI mode
        if "gui" in usernames:
            self.run_gui()
            return

        default_password = getattr(settings, "DEMO_USER_DEFAULT_PASSWORD", "demo")
        default_count = getattr(settings, "DEMO_USER_DEFAULT_COUNT", 1)
        default_gp_length = getattr(settings, "DEMO_USER_DEFAULT_GP_LENGTH", 8)
        default_output = getattr(settings, "DEMO_USER_DEFAULT_OUTPUT", "none")

        all_created_users = []

        for base_username in usernames:
            # ---------- Case-sensitive matching ----------
            existing_users = User.objects.filter(
                Q(username=base_username) |
                Q(username__regex=fr"^{base_username}[0-9]+")
            )

            # ---------- DELETE USERS ----------
            if options.get("delete"):
                count = existing_users.count()
                existing_users.delete()
                self.stdout.write(self.style.SUCCESS(f"🗑️ Deleted {count} users with base '{base_username}'"))
                continue

            # ---------- MODIFY USERS ----------
            if options.get("modify"):
                modifications = dict(pair.split("=", 1) for pair in options["modify"].split(","))
                users = existing_users
                if not users.exists():
                    self.stdout.write(self.style.WARNING(f"No users found with base username '{base_username}'"))
                    continue
                for user in users:
                    for field, value in modifications.items():
                        if field.lower() in ["pw", "password"]:
                            user.set_password(value)
                        else:
                            setattr(user, field, value)
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"✏️ Modified {user.username}"))
                continue

            # ---------- CREATE USERS ----------
            count = options.get("count") or default_count
            gp_length = options.get("gp") or default_gp_length
            skip_mode = options.get("skip", "fill")

            # Detect existing suffixes
            existing_numbers = set()
            for user in existing_users:
                suffix = user.username[len(base_username):]
                if suffix.isdigit():
                    existing_numbers.add(int(suffix))
            max_existing = max(existing_numbers) if existing_numbers else 0

            # Generate new numbers
            all_positions = list(range(1, max_existing + count + 1))
            gaps = [p for p in all_positions if p not in existing_numbers]
            new_numbers = []
            if skip_mode == "end":
                new_numbers = list(range(max_existing + 1, max_existing + count + 1))
            else:
                for i in range(len(gaps) - count + 1):
                    candidate = gaps[i:i + count]
                    if candidate[-1] - candidate[0] + 1 == count:
                        new_numbers = candidate
                        break
                if not new_numbers:
                    new_numbers = list(range(max_existing + 1, max_existing + count + 1))

            # Shared password
            shared_password = None
            if options.get("same_pass") and gp_length:
                shared_password = "".join(random.choices(string.ascii_letters + string.digits, k=gp_length))

            # Preview users
            preview_users = []
            for idx, num in enumerate(new_numbers):
                uname = f"{base_username}{num}" if count > 1 else base_username
                if gp_length:
                    pw = shared_password or "".join(random.choices(string.ascii_letters + string.digits, k=gp_length))
                else:
                    pw = options.get("password") or default_password
                preview_users.append({"username": uname, "password": pw})

            if options.get("sf"):
                self.stdout.write(self.style.WARNING(f"⚡ Preview of users to be created for base '{base_username}':"))
                for u in preview_users:
                    self.stdout.write(
                        f"{u['username']} | Password: {u['password']} | "
                        f"Staff={options['staff']} | Superuser={options['superuser']}"
                    )
                confirm = input("Create these users? (y/n): ").lower()
                if confirm != "y":
                    self.stdout.write(self.style.WARNING(f"Aborted creation for base '{base_username}'"))
                    continue

            # ---------- Create or skip existing users ----------
            created_users = []
            for u in preview_users:
                if User.objects.filter(username=u["username"]).exists():
                    self.stdout.write(self.style.WARNING(f"⚠️ User {u['username']} already exists. Skipping creation."))
                    created_users.append({
                        **u,
                        "staff": options.get("staff", False),
                        "superuser": options.get("superuser", False),
                        "login_ok": None,
                    })
                    continue

                user = User.objects.create_user(
                    username=u["username"],
                    password=u["password"],
                    is_staff=options.get("staff", False),
                    is_superuser=options.get("superuser", False)
                )
                login_ok = None
                if not options.get("skip_pw_check"):
                    login_ok = authenticate(username=u["username"], password=u["password"]) is not None
                created_users.append({
                    **u,
                    "staff": options.get("staff", False),
                    "superuser": options.get("superuser", False),
                    "login_ok": login_ok
                })
                self.stdout.write(self.style.SUCCESS(f"✅ User {u['username']} created | Password: {u['password']}"))

            all_created_users.extend(created_users)

        # ---------- OUTPUT / EXPORT ----------
        output_option = options.get("output")
        if output_option:
            if isinstance(output_option, list):
                output_type = output_option[0]
                version = output_option[1] if len(output_option) > 1 else "dev"
            else:
                output_type = output_option
                version = "dev"

            # If no users were created just now, gather existing users
            if not all_created_users:
                for base_username in usernames:
                    existing_users = User.objects.filter(
                        Q(username=base_username) | Q(username__regex=fr"^{base_username}[0-9]+")
                    )
                    for u in existing_users:
                        all_created_users.append({
                            "username": u.username,
                            "staff": u.is_staff,
                            "superuser": u.is_superuser,
                            "password": "(hidden)" if version == "user" else "(unknown)",
                            "login_ok": None
                        })

            # Adjust fields for user-friendly version
            if version == "user":
                for u in all_created_users:
                    u.pop("login_ok", None)
                    if u.get("password") == "(unknown)":
                        u["password"] = "(hidden)"

            out_path = Path(f"demo_users.{output_type}")
            if output_type == "txt":
                with open(out_path, "w") as f:
                    for u in all_created_users:
                        f.write(" | ".join(f"{k}={v}" for k, v in u.items()) + "\n")
            elif output_type == "csv":
                with open(out_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=list(all_created_users[0].keys()))
                    writer.writeheader()
                    writer.writerows(all_created_users)
            elif output_type == "json":
                with open(out_path, "w") as f:
                    json.dump(all_created_users, f, indent=2)
            elif output_type == "bat":
                with open(out_path, "w") as f:
                    for u in all_created_users:
                        f.write(f'net user {u["username"]} {u.get("password","")} /add\n')
            self.stdout.write(self.style.SUCCESS(f"📄 Output saved to {out_path}"))

        # ---------- Login Test ----------
        if options.get("logintest") and all_created_users:
            client = Client()
            for u in all_created_users:
                uname, pw = u["username"], u["password"]
                ok = client.login(username=uname, password=pw)
                self.stdout.write(self.style.SUCCESS(f"🔑 Login test {uname}: {'OK' if ok else 'FAILED'}"))

        # ---------- Visit URL ----------
        if options.get("visiturl"):
            client = Client()
            for u in all_created_users:
                client.login(username=u["username"], password=u["password"])
                resp = client.get(options["visiturl"])
                self.stdout.write(
                    self.style.SUCCESS(f"🌐 {u['username']} visited {options['visiturl']} → {resp.status_code}")
                )

        # ---------- Run view ----------
        if options.get("runview"):
            module_name, func_name = options["runview"].rsplit(".", 1)
            view_func = getattr(import_module(module_name), func_name)
            factory = RequestFactory()
            for u in all_created_users:
                request = factory.get("/")
                request.user = User.objects.get(username=u["username"])
                resp = view_func(request)
                code = getattr(resp, "status_code", "n/a")
                self.stdout.write(
                    self.style.SUCCESS(f"⚡ Ran view {options['runview']} as {u['username']} → {code}")
                )

        # ---------- Submit form ----------
        if options.get("form"):
            url, *pairs = options["form"]
            data = dict(f.split("=", 1) for f in pairs)
            client = Client()
            for u in all_created_users:
                client.login(username=u["username"], password=u["password"])
                resp = client.post(url, data)
                self.stdout.write(
                    self.style.SUCCESS(f"📨 {u['username']} submitted form {url} → {resp.status_code}")
                )
