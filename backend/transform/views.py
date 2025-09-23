from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
import pandas as pd
import io, re, json
from .llm import nl_to_regex
from .schemas import TransformRequest

TEXT_DTYPES = ("object", "string")

def extract_replacement_from_instruction(instruction: str) -> str:
    """Extract replacement value from instruction string."""
    instruction_lower = instruction.lower()
    
    # Try to extract replacement from common patterns
    if "replace" in instruction_lower:
        match = re.search(r"replace\s+(?:with|by)\s+['\"]?([^'\"]+)['\"]?", instruction, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    elif "change" in instruction_lower:
        # Handle patterns like "change Tom to John" or "change to VIC"
        match = re.search(r"change\s+(?:\w+\s+)?to\s+['\"]?([^'\"]+)['\"]?", instruction, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # Default replacement
    return "REDACTED"

def read_tabular(fbytes: bytes, filename: str) -> pd.DataFrame:
    fname = filename.lower()
    if fname.endswith(".csv"):
        return pd.read_csv(io.BytesIO(fbytes))
    if fname.endswith(".xls") or fname.endswith(".xlsx"):
        return pd.read_excel(io.BytesIO(fbytes))
    raise ValueError("Only CSV, XLS, XLSX are supported")

class TransformAPI(APIView):
    def post(self, request):
        try:
            file = request.FILES.get("file")
            payload = request.POST.get("payload")
            if not file or not payload:
                return Response({"detail": "file and payload are required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                df = read_tabular(file.read(), file.name)
            except Exception as e:
                return Response({"detail": f"Unsupported or invalid file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                req = TransformRequest.model_validate_json(payload)
            except Exception as e:
                return Response({"detail": f"Invalid payload: {e}"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                regex = nl_to_regex(req.instruction)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            # Extract replacement value from instruction
            replacement = extract_replacement_from_instruction(req.instruction)

            if req.columns:
                cols = [c for c in req.columns if c in df.columns]
            else:
                cols = [c for c in df.columns if c.lower() != 'id']  # Apply to all columns except 'id'

            try:
                pattern = re.compile(regex, re.IGNORECASE)
            except re.error as e:
                return Response({"detail": f"Invalid regex: {e}"}, status=status.HTTP_400_BAD_REQUEST)
            df_out = df.copy()
            for c in cols:
                df_out[c] = df_out[c].astype(str).str.replace(pattern, replacement, regex=True)

            return Response({
                "regexUsed": regex,
                "columnsApplied": cols,
                "columns": list(df_out.columns),
                "rowsOriginal": df.head(100).to_dict(orient="records"),
                "rows": df_out.head(100).to_dict(orient="records"),
                "totalRows": int(len(df_out)),
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class DownloadAPI(APIView):
    def post(self, request):
        try:
            file = request.FILES.get("file")
            payload = request.POST.get("payload")
            file_format = request.POST.get("format", "csv")  # csv, xlsx
            
            if not file or not payload:
                return Response({"detail": "file and payload are required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                df = read_tabular(file.read(), file.name)
            except Exception as e:
                return Response({"detail": f"Unsupported or invalid file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                req = TransformRequest.model_validate_json(payload)
            except Exception as e:
                return Response({"detail": f"Invalid payload: {e}"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                regex = nl_to_regex(req.instruction)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            # Extract replacement value from instruction
            replacement = extract_replacement_from_instruction(req.instruction)

            if req.columns:
                cols = [c for c in req.columns if c in df.columns]
            else:
                cols = [c for c in df.columns if c.lower() != 'id']  # Apply to all columns except 'id'

            try:
                pattern = re.compile(regex, re.IGNORECASE)
            except re.error as e:
                return Response({"detail": f"Invalid regex: {e}"}, status=status.HTTP_400_BAD_REQUEST)
            
            df_out = df.copy()
            for c in cols:
                df_out[c] = df_out[c].astype(str).str.replace(pattern, replacement, regex=True)

            # Generate file based on format
            if file_format.lower() == "xlsx":
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_out.to_excel(writer, index=False, sheet_name='Processed Data')
                output.seek(0)
                response = HttpResponse(
                    output.getvalue(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="processed_data.xlsx"'
            else:  # Default to CSV
                output = io.StringIO()
                df_out.to_csv(output, index=False)
                response = HttpResponse(
                    output.getvalue(),
                    content_type='text/csv'
                )
                response['Content-Disposition'] = f'attachment; filename="processed_data.csv"'
            
            return response
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)
